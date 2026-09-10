# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


from collections import defaultdict

import frappe
from frappe.utils import cint, flt, getdate, rounded

from hrms.payroll.doctype.employee_benefit_ledger.employee_benefit_ledger import (
	create_employee_benefit_ledger_entry,
)
from hrms.payroll.doctype.payroll_period.payroll_period import get_period_factor
from hrms.payroll.doctype.salary_slip.salary_slip_utils import get_benefits_details_parent
from hrms.payroll.utils import get_salary_component_data


class BenefitsMixin:
	def create_benefits_ledger_entry(self):
		if self.benefit_ledger_components:
			args = {
				"payroll_period": self.payroll_period.name,
				"benefit_ledger_components": self.benefit_ledger_components,
				"benefit_details_parent": self.benefit_details_parent,
				"benefit_details_doctype": self.benefit_details_doctype,
			}
			create_employee_benefit_ledger_entry(self, args)

	def add_employee_benefits(self):
		# Fetch employee benefits based on mandatory benefit application setting, get amounts for accrual or payouts for each and add to salary slip accrued_benefits/earnings table
		if not self.payroll_period:
			return

		self.benefit_details_parent, self.benefit_details_doctype = get_benefits_details_parent(
			self.employee, self.payroll_period.name, self._salary_structure_assignment.name
		)

		if not self.benefit_details_parent:
			return

		SalaryComponent = frappe.qb.DocType("Salary Component")
		EmployeeBenefitDetail = frappe.qb.DocType(self.benefit_details_doctype)
		employee_benefits = (
			frappe.qb.from_(EmployeeBenefitDetail)
			.join(SalaryComponent)
			.on(EmployeeBenefitDetail.salary_component == SalaryComponent.name)
			.select(
				EmployeeBenefitDetail.salary_component,
				EmployeeBenefitDetail.amount.as_("yearly_amount"),
				SalaryComponent.payout_method,
				SalaryComponent.depends_on_payment_days,
				SalaryComponent.round_to_the_nearest_integer,
				SalaryComponent.final_cycle_accrual_payout,
			)
			.where(EmployeeBenefitDetail.parent == self.benefit_details_parent)
			.where(SalaryComponent.is_flexible_benefit == 1)
			.where(SalaryComponent.accrual_component == 1)
			.run(as_dict=True)
		)

		if employee_benefits:
			employee_benefits = self.get_current_period_employee_benefit_amounts(employee_benefits)
			self.add_current_period_employee_benefits(employee_benefits)

	def add_current_period_employee_benefits(self, employee_benefits: dict):
		"""Add flexible benefit payouts and accruals to salary slip Accrued Benefits table. Maintain benefit_ledger_components list to track accruals and payouts in this payroll cycle to be added to Employee Benefit Ledger."""
		for benefit in employee_benefits:
			if benefit.amount <= 0:
				continue

			earning_component = get_salary_component_data(benefit.salary_component)
			if not earning_component.is_flexible_benefit:
				continue

			if benefit.is_accrual:
				self.append(
					"accrued_benefits",
					{
						"salary_component": benefit.salary_component,
						"amount": benefit.amount,
					},
				)
			else:
				self.update_component_row(
					earning_component,
					benefit.amount,
					"earnings",
				)

			transaction_type = "Accrual" if benefit.is_accrual else "Payout"
			remarks = "Pro rata flexible benefit accrual" if benefit.is_accrual else "Flexible benefit payout"

			self.benefit_ledger_components.append(
				{
					"salary_component": benefit.salary_component,
					"is_accrual": benefit.is_accrual,
					"amount": flt(benefit.amount),
					"transaction_type": transaction_type,
					"flexible_benefit": 1,
					"yearly_benefit": benefit.get("yearly_amount", 0),
					"remarks": remarks,
				}
			)

	def get_current_period_employee_benefit_amounts(self, employee_benefits: dict) -> dict:
		"""Calculate employee benefit amounts for the current salary slip period based on payout method."""

		is_last_payroll_cycle = False
		if self.payroll_period and getdate(self.payroll_period.end_date) <= getdate(self.end_date):
			is_last_payroll_cycle = True

		total_sub_periods = get_period_factor(
			self.employee,
			self.start_date,
			self.end_date,
			self.payroll_frequency,
			self.payroll_period,
		)[0]

		ledger_map = self._get_benefit_ledger_entries(employee_benefits)
		precision = frappe.get_precision("Employee Benefit Detail", "amount")

		# Process each benefit according to its payout method
		for benefit in employee_benefits:
			current_period_benefit = benefit.yearly_amount / total_sub_periods if total_sub_periods else 0
			if benefit.depends_on_payment_days:
				current_period_benefit = (
					flt(current_period_benefit) * flt(self.payment_days) / cint(self.total_working_days)
				)

			# Get accrued and paid totals for this benefit
			total_accrued = ledger_map[benefit.salary_component].get("Accrual", 0)
			total_paid = ledger_map[benefit.salary_component].get("Payout", 0)

			current_period_benefit, is_accrual = self._get_benefit_amount_and_transaction_type(
				benefit, current_period_benefit, total_accrued, total_paid, is_last_payroll_cycle
			)

			current_period_benefit = flt(current_period_benefit, precision)
			if benefit.round_to_the_nearest_integer:
				current_period_benefit = rounded(current_period_benefit or 0)
			benefit.is_accrual = is_accrual
			benefit.amount = current_period_benefit

		return employee_benefits

	def _get_benefit_ledger_entries(self, employee_benefits):
		"""Fetch existing benefit ledger entries and map amounts by benefit salary component and transaction type."""

		ledger_entries = frappe.get_all(
			"Employee Benefit Ledger",
			filters={
				"employee": self.employee,
				"salary_component": ["in", [benefit.salary_component for benefit in employee_benefits]],
				"payroll_period": self.payroll_period.name,
			},
			fields=["salary_component", "transaction_type", "amount"],
		)
		benefit_ledger_map = defaultdict(lambda: defaultdict(float))
		for entry in ledger_entries:
			benefit_ledger_map[entry["salary_component"]][entry["transaction_type"]] += entry["amount"]

		return benefit_ledger_map

	def _get_benefit_amount_and_transaction_type(
		self, benefit, current_period_benefit, total_accrued, total_paid, is_last_payroll_cycle
	):  # Process according to payout method
		is_accrual = 1

		if benefit.payout_method == "Accrue and payout at end of payroll period":
			current_period_benefit, is_accrual = self._get_final_period_benefit_payout(
				benefit, current_period_benefit, total_accrued, total_paid, is_last_payroll_cycle
			)
		elif benefit.payout_method == "Accrue per cycle, pay only on claim":
			current_period_benefit, is_accrual = self._get_claim_based_benefit_payout(
				benefit, current_period_benefit, total_accrued, total_paid, is_last_payroll_cycle
			)

		return current_period_benefit, is_accrual

	def _get_final_period_benefit_payout(
		self, benefit, current_period_benefit, total_accrued, total_paid, is_last_payroll_cycle
	):
		"""Process 'Accrue and payout at end of payroll period' benefit"""
		is_accrual = 1
		benefit_claims = [
			row
			for row in self.earnings
			if row.salary_component == benefit.salary_component and getattr(row, "additional_salary", None)
		]  # Any claims for this benefit component to be paid via additional salary in this payroll cycle
		claimed_amount = sum(row.amount for row in benefit_claims) if benefit_claims else 0
		total_paid += claimed_amount

		if 0 < (benefit.yearly_amount - total_accrued) < current_period_benefit:
			current_period_benefit = (
				benefit.yearly_amount - total_accrued
			)  # Limit benefit amount to remaining yearly amount

		if is_last_payroll_cycle:  # On last payroll cycle, pay out all accrued benefits
			current_period_benefit = max(total_accrued + current_period_benefit - total_paid, 0)
			is_accrual = 0

		return current_period_benefit, is_accrual

	def _get_claim_based_benefit_payout(
		self, benefit, current_period_benefit, total_accrued, total_paid, is_last_payroll_cycle
	):
		"""Process 'Accrue per cycle, pay only on claim' benefits.
		Always record the full entitlement for the current cycle, even if part of it
		was already claimed. This ensures the Employee Benefit Ledger shows
		the correct total entitlement for accurate future claim balance calculations.
		"""
		is_accrual = 1
		benefit_claims = [
			row
			for row in self.earnings
			if row.salary_component == benefit.salary_component and getattr(row, "additional_salary", None)
		]
		claimed_amount = sum(row.amount for row in benefit_claims) if benefit_claims else 0
		total_paid += claimed_amount

		# if more was paid than accrued, reduce current period accrual accordingly
		if total_paid > total_accrued:
			current_period_benefit -= total_paid - total_accrued

		if 0 < (benefit.yearly_amount - total_accrued) < current_period_benefit:
			current_period_benefit = (
				benefit.yearly_amount - total_accrued
			)  # Limit benefit amount to remaining yearly amount

		# Pay out all unclaimed benefits in final cycle if final payout option is enabled
		if is_last_payroll_cycle and benefit.final_cycle_accrual_payout:
			current_period_benefit = max(total_accrued + current_period_benefit - total_paid, 0)
			is_accrual = 0

		return current_period_benefit, is_accrual
