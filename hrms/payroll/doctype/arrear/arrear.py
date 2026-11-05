# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.functions import Sum
from frappe.utils import flt, getdate

from hrms.payroll.doctype.employee_benefit_ledger.employee_benefit_ledger import (
	delete_employee_benefit_ledger_entry,
)
from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip


class Arrear(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.payroll.doctype.arrear_salary_slip_detail.arrear_salary_slip_detail import (
			ArrearSalarySlipDetail,
		)
		from hrms.payroll.doctype.payroll_correction_child.payroll_correction_child import (
			PayrollCorrectionChild,
		)

		accrual_arrears: DF.Table[PayrollCorrectionChild]
		amended_from: DF.Link | None
		arrear_start_date: DF.Date
		company: DF.Link
		currency: DF.Link
		deduction_arrears: DF.Table[PayrollCorrectionChild]
		earning_arrears: DF.Table[PayrollCorrectionChild]
		employee: DF.Link
		employee_name: DF.Data | None
		payroll_date: DF.Date
		payroll_period: DF.Link
		salary_slip_arrears: DF.Table[ArrearSalarySlipDetail]
		salary_structure: DF.Link
	# end: auto-generated types

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
			sum_by_component(existing_components), sum_by_component(new_structure_components)
		)

		if component_differences:
			self.populate_arrear_tables(component_differences)
			self.populate_salary_slip_arrears(
				existing_components, new_structure_components, component_differences
			)

	def get_existing_salary_slips(self):
		salary_slips = []

		if self.employee and self.arrear_start_date:
			filters = {
				"employee": self.employee,
				"company": self.company,
				"docstatus": 1,
				"start_date": (">=", self.arrear_start_date),
				"end_date": ("<=", self.payroll_period_details.end_date),
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
		Returns a dict: {"earnings": {slip: {component: amount}}, "deductions": {...}, "accruals": {...}}
		"""
		SalarySlipDetail = frappe.qb.DocType("Salary Detail")
		SalaryComponent = frappe.qb.DocType("Salary Component")

		slip_details = (
			frappe.qb.from_(SalarySlipDetail)
			.join(SalaryComponent)
			.on(SalarySlipDetail.salary_component == SalaryComponent.name)
			.select(
				SalarySlipDetail.parent,
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

		existing = {"earnings": {}, "deductions": {}, "accruals": {}}

		for detail in slip_details:
			if detail.parentfield in ("earnings", "deductions"):
				add_amount(
					existing[detail.parentfield], detail.parent, detail.salary_component, detail.amount
				)

		existing["accruals"] = self.fetch_existing_accrual_components(salary_slips)

		# Include submitted Payroll Corrections and earlier Arrears for these salary slips
		for adjustments in (
			self.fetch_existing_payroll_corrections(salary_slips),
			self.fetch_existing_arrears(salary_slips),
		):
			for section, slips in adjustments.items():
				for slip, components in slips.items():
					for component, amount in components.items():
						add_amount(existing[section], slip, component, amount)

		if not any(existing.values()):
			frappe.throw(_("No arrear components found in the existing salary slips."))

		return existing

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
				AccruedBenefit.parent,
				AccruedBenefit.salary_component,
				AccruedBenefit.amount,
			)
			.where((AccruedBenefit.parent.isin(salary_slips)) & (SalaryComponent.arrear_component == 1))
		).run(as_dict=True)

		accruals = {}
		for detail in accrual_details:
			add_amount(accruals, detail.parent, detail.salary_component, detail.amount)

		return accruals

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
				PayrollCorrection.salary_slip_reference,
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

		sections = {
			"earning_arrears": "earnings",
			"deduction_arrears": "deductions",
			"accrual_arrears": "accruals",
		}
		existing = {"earnings": {}, "deductions": {}, "accruals": {}}
		for detail in corrections:
			if section := sections.get(detail.parentfield):
				add_amount(
					existing[section], detail.salary_slip_reference, detail.salary_component, detail.amount
				)

		return existing

	def fetch_existing_arrears(self, salary_slips: list):
		existing = {"earnings": {}, "deductions": {}, "accruals": {}}
		if not salary_slips:
			return existing

		Arrear = frappe.qb.DocType("Arrear")
		ArrearDetail = frappe.qb.DocType("Arrear Salary Slip Detail")

		arrears = (
			frappe.qb.from_(Arrear)
			.join(ArrearDetail)
			.on(Arrear.name == ArrearDetail.parent)
			.select(
				ArrearDetail.salary_slip,
				ArrearDetail.arrear_type,
				ArrearDetail.salary_component,
				ArrearDetail.amount,
			)
			.where(
				(ArrearDetail.parenttype == "Arrear")
				& (ArrearDetail.salary_slip.isin(salary_slips))
				& (Arrear.docstatus == 1)
				& (Arrear.name != (self.name or ""))
			)
		).run(as_dict=True)

		sections = {"Earning": "earnings", "Deduction": "deductions", "Accrual": "accruals"}
		for detail in arrears:
			add_amount(
				existing[sections[detail.arrear_type]],
				detail.salary_slip,
				detail.salary_component,
				detail.amount,
			)

		return existing

	def generate_preview_components(self, salary_slips: list):
		# Generate preview salary slip with new salary structure and return component and amounts.
		if not salary_slips:
			return {}

		preview = {"earnings": {}, "deductions": {}, "accruals": {}}

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
					add_amount(preview["earnings"], slip.name, row.salary_component, row.amount)

			# deductions
			for row in preview_slip.get("deductions", []) or []:
				if (
					not getattr(row, "additional_salary", None)
					and not getattr(row, "variable_based_on_taxable_salary", False)
					and is_arrear_component(row.salary_component)
				):
					add_amount(preview["deductions"], slip.name, row.salary_component, row.amount)

			# accruals
			for row in getattr(preview_slip, "accrued_benefits", []) or []:
				if is_arrear_component(row.salary_component):
					add_amount(preview["accruals"], slip.name, row.salary_component, row.amount)

		return preview

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

	def populate_salary_slip_arrears(
		self, existing_components: dict, new_components: dict, component_differences: dict
	):
		# per-slip breakdown of the arrears paid, so that later Arrears for these slips can subtract it
		self.set("salary_slip_arrears", [])
		arrear_types = {"earnings": "Earning", "deductions": "Deduction", "accruals": "Accrual"}

		for section, components in component_differences.items():
			new_slips = new_components.get(section, {})
			existing_slips = existing_components.get(section, {})
			for slip in sorted(set(new_slips) | set(existing_slips)):
				for component in components:
					amount = flt(new_slips.get(slip, {}).get(component)) - flt(
						existing_slips.get(slip, {}).get(component)
					)
					if amount:
						self.append(
							"salary_slip_arrears",
							{
								"salary_slip": slip,
								"arrear_type": arrear_types[section],
								"salary_component": component,
								"amount": amount,
							},
						)

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


def add_amount(target: dict, salary_slip: str, component: str, amount: float):
	components = target.setdefault(salary_slip, {})
	components[component] = components.get(component, 0.0) + flt(amount)


def sum_by_component(components_by_slip: dict) -> dict:
	totals = {}
	for section, slips in components_by_slip.items():
		section_totals = totals.setdefault(section, {})
		for components in slips.values():
			for component, amount in components.items():
				section_totals[component] = section_totals.get(component, 0.0) + amount
	return totals
