# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.functions import Sum
from frappe.utils import getdate

from hrms.payroll.doctype.employee_benefit_ledger.employee_benefit_ledger import (
	delete_employee_benefit_ledger_entry,
)
from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip


class Arrear(Document):
	@property
	def payroll_period_details(self):
		if not hasattr(self, "__payroll_period_details"):
			self.__payroll_period_details = frappe.get_doc("Payroll Period", self.payroll_period)
		return self.__payroll_period_details

	def validate(self):
		self.validate_dates()
		self.validate_salary_structure_assignment()
		self.validate_duplicate_doc()
		self.calculate_salary_structure_arrears()

	def on_submit(self):
		self.validate_arrear_details()
		self.create_additional_salary()
		self.create_benefit_ledger_entry()

	def on_cancel(self):
		delete_employee_benefit_ledger_entry("reference_document", self.name)

	def validate_dates(self):
		if self.arrear_start_date and self.payroll_period:
			if getdate(self.arrear_start_date) < self.payroll_period_details.start_date:
				frappe.throw(
					_("From Date {0} cannot be before Payroll Period start date {1}").format(
						self.arrear_start_date, self.payroll_period_details.start_date
					)
				)
			elif getdate(self.arrear_start_date) > (self.payroll_period_details.end_date):
				frappe.throw(
					_("From Date {0} cannot be after Payroll Period end date {1}").format(
						self.arrear_start_date, self.payroll_period_details.end_date
					)
				)

	def validate_salary_structure_assignment(self):
		# Validate salary structure assignment exists for the employee and salary structure
		if not (self.employee and self.salary_structure and self.payroll_period):
			return

		assignment = frappe.db.get_value(
			"Salary Structure Assignment",
			{
				"employee": self.employee,
				"salary_structure": self.salary_structure,
				"docstatus": 1,
				"from_date": (">=", self.arrear_start_date),
			},
			["name", "from_date"],
			as_dict=True,
		)

		if not assignment:
			frappe.throw(
				_(
					"No active Salary Structure Assignment found for employee {0} with salary structure {1} on or after arrear start date {2}"  # TODO: make error message better
				).format(
					frappe.bold(self.employee),
					frappe.bold(self.salary_structure),
					frappe.bold(self.arrear_start_date) or "",
				)
			)

	def validate_duplicate_doc(self):
		if frappe.db.exists(
			"Arrear",
			{
				"employee": self.employee,
				"salary_structure": self.salary_structure,
				"payroll_period": self.payroll_period,
				"docstatus": 1,
				"name": ["!=", self.name],
			},
		):
			frappe.throw(
				_(
					"An Arrear document already exists for employee {0} with salary structure {1} in payroll period {2}"
				).format(
					frappe.bold(self.employee),
					frappe.bold(self.salary_structure),
					frappe.bold(self.payroll_period),
				)
			)

	def calculate_salary_structure_arrears(self):
		# calculate arrear amounts for each component across processed salary slips and populate child tables
		existing_salary_slips = self.get_existing_salary_slips()
		salary_slip_names = [slip.get("name") for slip in existing_salary_slips]

		# Existing components from processed slips
		existing_components = self.fetch_existing_salary_components(salary_slip_names)
		# Preview components using the new salary structure
		new_structure_components = self.generate_preview_components(existing_salary_slips)

		component_differences = self.compute_component_differences(
			existing_components, new_structure_components
		)

		if component_differences:
			self.populate_arrear_tables(component_differences)

	def get_existing_salary_slips(self):
		salary_slips = []

		if self.employee and self.arrear_start_date:
			filters = {
				"employee": self.employee,
				"docstatus": 1,
				"start_date": (">=", self.arrear_start_date),
			}

			salary_slips = frappe.get_all(
				"Salary Slip",
				filters=filters,
				fields=["name", "posting_date", "start_date", "end_date"],
				order_by="start_date",
			)
		if not salary_slips:
			frappe.throw(
				_("No salary slips found for the selected employee from {0}").format(self.arrear_start_date)
			)

		return salary_slips

	def fetch_existing_salary_components(self, salary_slips: list):
		"""Fetch salary components and amounts from existing salary slips with arrear_component enabled.
		Returns a dict: {"earnings": {component: total}, "deductions": {component: total}, "accruals": {component: total}}
		"""
		SalarySlipDetail = frappe.qb.DocType("Salary Detail")
		SalaryComponent = frappe.qb.DocType("Salary Component")

		slip_details = (
			frappe.qb.from_(SalarySlipDetail)
			.join(SalaryComponent)
			.on(SalarySlipDetail.salary_component == SalaryComponent.name)
			.select(
				SalarySlipDetail.parentfield,
				SalarySlipDetail.salary_component,
				SalarySlipDetail.amount,
			)
			.where(
				(SalarySlipDetail.parent.isin(salary_slips))
				& (SalarySlipDetail.additional_salary.isnull())
				& (SalarySlipDetail.variable_based_on_taxable_salary == 0)
				& (SalaryComponent.arrear_component == 1)
			)
		).run(as_dict=True)

		earnings_totals = {}
		deductions_totals = {}

		# Sum amounts per component grouped by parentfield
		for detail in slip_details:
			comp = detail.salary_component
			amt = detail.amount
			parentfield = detail.parentfield
			if parentfield == "earnings":
				earnings_totals[comp] = earnings_totals.get(comp, 0.0) + amt
			elif parentfield == "deductions":
				deductions_totals[comp] = deductions_totals.get(comp, 0.0) + amt

		accrual_totals = self.fetch_existing_accrual_components(salary_slips)

		# Fetch and include existing Payroll Correction amounts for these salary slips
		payroll_correction_totals = self.fetch_existing_payroll_corrections(salary_slips)

		# Add payroll correction amounts to existing component totals
		for component, amount in payroll_correction_totals.get("earnings", {}).items():
			earnings_totals[component] = earnings_totals.get(component, 0.0) + amount

		for component, amount in payroll_correction_totals.get("deductions", {}).items():
			deductions_totals[component] = deductions_totals.get(component, 0.0) + amount

		for component, amount in payroll_correction_totals.get("accruals", {}).items():
			accrual_totals[component] = accrual_totals.get(component, 0.0) + amount

		if not (earnings_totals or deductions_totals or accrual_totals):
			frappe.throw(_("No arrear components found in the existing salary slips."))

		return {"earnings": earnings_totals, "deductions": deductions_totals, "accruals": accrual_totals}

	def fetch_existing_accrual_components(self, salary_slips: list):
		"""Fetch accrual components from existing salary slips with arrear_component enabled."""
		if not salary_slips:
			return {}

		AccruedBenefit = frappe.qb.DocType("Employee Benefit Detail")
		SalaryComponent = frappe.qb.DocType("Salary Component")

		accrual_details = (
			frappe.qb.from_(AccruedBenefit)
			.inner_join(SalaryComponent)
			.on(AccruedBenefit.salary_component == SalaryComponent.name)
			.select(
				AccruedBenefit.salary_component,
				AccruedBenefit.amount,
			)
			.where((AccruedBenefit.parent.isin(salary_slips)) & (SalaryComponent.arrear_component == 1))
		).run(as_dict=True)

		accrual_totals = {}
		for detail in accrual_details:
			comp = detail.get("salary_component")
			amt = detail.get("amount", 0.0)
			accrual_totals[comp] = accrual_totals.get(comp, 0.0) + amt

		return accrual_totals

	def fetch_existing_payroll_corrections(self, salary_slips: list):
		# fetch payroll correction amounts for existing salary slips with arrear_component enabled.
		if not salary_slips:
			return {"earnings": {}, "deductions": {}, "accruals": {}}

		PayrollCorrection = frappe.qb.DocType("Payroll Correction")
		PCChild = frappe.qb.DocType("Payroll Correction Child")
		SalaryComponent = frappe.qb.DocType("Salary Component")

		corrections = (
			frappe.qb.from_(PayrollCorrection)
			.join(PCChild)
			.on(PayrollCorrection.name == PCChild.parent)
			.join(SalaryComponent)
			.on(PCChild.salary_component == SalaryComponent.name)
			.select(
				PCChild.parentfield,
				PCChild.salary_component,
				PCChild.amount,
			)
			.where(
				(PayrollCorrection.salary_slip_reference.isin(salary_slips))
				& (PayrollCorrection.docstatus == 1)
				& (SalaryComponent.arrear_component == 1)
			)
		).run(as_dict=True)

		earnings_totals = {}
		deductions_totals = {}
		accrual_totals = {}

		# Sum corrections per component grouped by parentfield
		for detail in corrections:
			comp = detail.salary_component
			amt = detail.amount or 0.0
			parentfield = detail.parentfield

			if parentfield == "earning_arrears":
				earnings_totals[comp] = earnings_totals.get(comp, 0.0) + amt
			elif parentfield == "deduction_arrears":
				deductions_totals[comp] = deductions_totals.get(comp, 0.0) + amt
			elif parentfield == "accrual_arrears":
				accrual_totals[comp] = accrual_totals.get(comp, 0.0) + amt

		return {"earnings": earnings_totals, "deductions": deductions_totals, "accruals": accrual_totals}

	def generate_preview_components(self, salary_slips: list):
		# Generate preview salary slip with new salary structure and return component and amounts.
		if not salary_slips:
			return {}

		preview_earnings = {}
		preview_deductions = {}
		preview_accruals = {}

		def is_arrear_component(component):
			return frappe.get_cached_value("Salary Component", component, "arrear_component")

		for slip in salary_slips:
			# Build a preview salary slip doc
			salary_slip_doc = frappe.get_doc(
				{
					"doctype": "Salary Slip",
					"employee": self.employee,
					"salary_structure": self.salary_structure,
					"posting_date": slip.get("posting_date"),
					"start_date": slip.get("start_date"),
					"end_date": slip.get("end_date"),
				}
			)

			# check if any Payroll Corrections exist for this slip and sum days_to_reverse to get actual payment days for when previewing salary slip for new structure
			PayrollCorrection = frappe.qb.DocType("Payroll Correction")
			total_days_to_reverse = (
				frappe.qb.from_(PayrollCorrection)
				.select(Sum(PayrollCorrection.days_to_reverse).as_("total_days"))
				.where(
					(PayrollCorrection.salary_slip_reference == slip.name)
					& (PayrollCorrection.docstatus == 1)
				)
			).run(pluck=True)
			total_days_to_reverse = total_days_to_reverse[0] or 0.0

			preview_slip = make_salary_slip(
				self.salary_structure,
				salary_slip_doc,
				self.employee,
				lwp_days_corrected=total_days_to_reverse,
			)

			# earnings
			for row in preview_slip.get("earnings", []) or []:
				if (not getattr(row, "additional_salary", None)) and is_arrear_component(
					row.salary_component
				):
					preview_earnings[row.salary_component] = preview_earnings.get(
						row.salary_component, 0.0
					) + getattr(row, "amount", 0.0)

			# deductions
			for row in preview_slip.get("deductions", []) or []:
				if (
					not getattr(row, "additional_salary", None)
					and not getattr(row, "variable_based_on_taxable_salary", False)
					and is_arrear_component(row.salary_component)
				):
					preview_deductions[row.salary_component] = preview_deductions.get(
						row.salary_component, 0.0
					) + getattr(row, "amount", 0.0)

			# accruals
			for row in getattr(preview_slip, "accrued_benefits", []) or []:
				if is_arrear_component(row.salary_component):
					preview_accruals[row.salary_component] = preview_accruals.get(
						row.salary_component, 0.0
					) + getattr(row, "amount", 0.0)

		return {"earnings": preview_earnings, "deductions": preview_deductions, "accruals": preview_accruals}

	def compute_component_differences(self, existing_components: dict, new_components: dict):
		"""Calculate component differences between existing and preview salary slips.
		existing_components and new_components params are dicts with keys 'earnings','deductions','accruals'
		"""
		if not existing_components:
			existing_components = {"earnings": {}, "deductions": {}, "accruals": {}}
		if not new_components:
			new_components = {"earnings": {}, "deductions": {}, "accruals": {}}

		earnings_diff = {}
		deductions_diff = {}
		accruals_diff = {}

		# earnings
		for comp, amount in new_components.get("earnings", {}).items():
			existing_amount = existing_components.get("earnings", {}).get(comp, 0.0)
			diff = amount - existing_amount
			if diff > 0:
				earnings_diff[comp] = diff

		# deductions
		for comp, amount in new_components.get("deductions", {}).items():
			existing_amount = existing_components.get("deductions", {}).get(comp, 0.0)
			diff = amount - existing_amount
			if diff > 0:
				deductions_diff[comp] = diff

		# accruals
		for comp, amount in new_components.get("accruals", {}).items():
			existing_amount = existing_components.get("accruals", {}).get(comp, 0.0)
			diff = amount - existing_amount
			if diff > 0:
				accruals_diff[comp] = diff

		result = {}
		if earnings_diff or deductions_diff or accruals_diff:
			result = {"earnings": earnings_diff, "deductions": deductions_diff, "accruals": accruals_diff}

		if not result:
			frappe.throw(
				_("There are no arrear differences between existing and new salary structure components.")
			)

		return result

	def populate_arrear_tables(self, component_differences: dict):
		# populate arrear amounts into child tables on this doc
		self.set("earning_arrears", [])
		self.set("deduction_arrears", [])
		self.set("accrual_arrears", [])

		for comp, total_amount in component_differences.get("earnings", {}).items():
			self.append("earning_arrears", {"salary_component": comp, "amount": total_amount})

		for comp, total_amount in component_differences.get("deductions", {}).items():
			self.append("deduction_arrears", {"salary_component": comp, "amount": total_amount})

		for comp, total_amount in component_differences.get("accruals", {}).items():
			self.append("accrual_arrears", {"salary_component": comp, "amount": total_amount})

	def validate_arrear_details(self):
		# Ensure that there are arrear details to process
		if not (self.earning_arrears or self.deduction_arrears or self.accrual_arrears):
			frappe.throw(_("No arrear details found"))

	def create_additional_salary(self):
		for component in (self.earning_arrears or []) + (self.deduction_arrears or []):
			if not component.salary_component or not component.amount:
				continue

			additional_salary = frappe.get_doc(
				{
					"doctype": "Additional Salary",
					"employee": self.employee,
					"company": self.company,
					"payroll_date": self.payroll_date,
					"salary_component": component.salary_component,
					"currency": self.currency,
					"amount": component.amount,
					"ref_doctype": "Arrear",
					"ref_docname": self.name,
					"overwrite_salary_structure_amount": 0,
				}
			)
			additional_salary.insert()
			additional_salary.submit()

	def create_benefit_ledger_entry(self):
		for component in self.accrual_arrears or []:
			if not component.salary_component or not component.amount:
				continue

			is_flexible_benefit = frappe.db.get_value(
				"Salary Component", component.salary_component, "is_flexible_benefit"
			)

			frappe.get_doc(
				{
					"doctype": "Employee Benefit Ledger",
					"employee": self.employee,
					"employee_name": self.employee_name,
					"company": self.company,
					"payroll_period": self.payroll_period,
					"salary_component": component.salary_component,
					"transaction_type": "Accrual",
					"amount": component.amount,
					"reference_doctype": "Arrear",
					"reference_document": self.name,
					"remarks": "Accrual via Arrears",
					"flexible_benefit": is_flexible_benefit,
				}
			).insert()
