# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from frappe.utils import flt, get_link_to_form, getdate

from hrms.payroll.doctype.income_tax_slab.income_tax_slab import calculate_tax_by_tax_slab
from hrms.payroll.utils import TAX_COMPONENTS_BY_COMPANY, get_salary_component_data


class IncomeTaxMixin:
	def compute_income_tax_breakup(self):
		if not self.payroll_period:
			return

		self.standard_tax_exemption_amount = 0
		self.tax_exemption_declaration = 0
		self.deductions_before_tax_calculation = 0

		self.non_taxable_earnings = self.compute_non_taxable_earnings()

		self.ctc = self.compute_ctc()

		self.income_from_other_sources = self.get_income_form_other_sources()

		self.total_earnings = self.ctc + self.income_from_other_sources

		if hasattr(self, "tax_slab"):
			if self.tax_slab.allow_tax_exemption:
				self.standard_tax_exemption_amount = self.tax_slab.standard_tax_exemption_amount
				self.deductions_before_tax_calculation = (
					self.compute_annual_deductions_before_tax_calculation()
				)

			self.tax_exemption_declaration = (
				self.get_total_exemption_amount() - self.standard_tax_exemption_amount
			)

		self.annual_taxable_amount = self.total_earnings - (
			self.non_taxable_earnings
			+ self.deductions_before_tax_calculation
			+ self.tax_exemption_declaration
			+ self.standard_tax_exemption_amount
		)

		self.income_tax_deducted_till_date = self.get_income_tax_deducted_till_date()

		if hasattr(self, "total_structured_tax_amount") and hasattr(self, "current_structured_tax_amount"):
			self.future_income_tax_deductions = (
				self.total_structured_tax_amount
				+ self.get("full_tax_on_additional_earnings", 0)
				- self.income_tax_deducted_till_date
			)

			self.current_month_income_tax = self.get("current_tax_amount", 0)

			# non included current_month_income_tax separately as its already considered
			# while calculating income_tax_deducted_till_date

			self.total_income_tax = self.income_tax_deducted_till_date + self.future_income_tax_deductions

	def compute_ctc(self):
		if hasattr(self, "previous_taxable_earnings"):
			return (
				self.previous_taxable_earnings_before_exemption
				+ self.current_structured_taxable_earnings_before_exemption
				+ self.future_structured_taxable_earnings_before_exemption
				+ self.current_additional_earnings
				+ self.unclaimed_taxable_benefits
				+ self.non_taxable_earnings
			)

		return 0.0

	def get_income_tax_deducted_till_date(self):
		tax_deducted = 0.0
		for tax_component in self.get("_component_based_variable_tax") or {}:
			tax_deducted += (
				self._component_based_variable_tax[tax_component]["previous_total_paid_taxes"]
				+ self._component_based_variable_tax[tax_component]["current_tax_amount"]
			)
		return tax_deducted

	def add_tax_components(self):
		# Calculate variable_based_on_taxable_salary after all components updated in salary slip
		tax_components, self.other_deduction_components = [], []
		for d in self.evaluated_components["deductions"]:
			if d.variable_based_on_taxable_salary == 1 and not d.formula and not flt(d.amount):
				tax_components.append(d.salary_component)
			else:
				self.other_deduction_components.append(d.salary_component)

		# consider manually added tax component
		if not tax_components:
			tax_components = [
				d.salary_component for d in self.get("deductions") if d.variable_based_on_taxable_salary
			]

		if self.is_new() and not tax_components:
			tax_components = self.get_tax_components()
			frappe.msgprint(
				_(
					"Added tax components from the Salary Component master as the salary structure didn't have any tax component."
				),
				indicator="blue",
				alert=True,
			)

		self._component_based_variable_tax = {}
		if tax_components and self.payroll_period and self.salary_structure:
			self.tax_slab = self.get_income_tax_slabs()
			self.compute_taxable_earnings_for_year()

		if self.handle_additional_salary_tax_component():
			self._component_based_variable_tax.setdefault(self.additional_salary_component, {})
			self.calculate_variable_tax(self.additional_salary_component, True)
			return

		for tax_component in tax_components:
			self._component_based_variable_tax.setdefault(tax_component, {})
			self.calculate_variable_based_on_taxable_salary(tax_component)
			if self._component_based_variable_tax[tax_component]:
				tax_amount = self._component_based_variable_tax[tax_component]["current_tax_amount"]
				tax_row = get_salary_component_data(tax_component)
				self.update_component_row(tax_row, tax_amount, "deductions")

	def get_tax_components(self) -> list:
		"""
		Returns:
		        list: A list of tax components specific to the company.
		        If no tax components are defined for the company,
		        it returns the default tax components.
		"""
		tax_components = frappe.cache().get_value(
			TAX_COMPONENTS_BY_COMPANY, self._fetch_tax_components_by_company
		)

		default_tax_components = tax_components.get("default", [])
		return tax_components.get(self.company, default_tax_components)

	def _fetch_tax_components_by_company(self) -> dict:
		"""
		Returns:
		    dict: A dictionary containing tax components grouped by company.

		Raises:
		    None
		"""

		tax_components = {}
		sc = frappe.qb.DocType("Salary Component")
		sca = frappe.qb.DocType("Salary Component Account")

		components = (
			frappe.qb.from_(sc)
			.left_join(sca)
			.on(sca.parent == sc.name)
			.select(
				sc.name,
				sca.company,
			)
			.where(sc.variable_based_on_taxable_salary == 1)
			.where(sc.disabled == 0)
		).run(as_dict=True)

		for component in components:
			key = component.company or "default"
			tax_components.setdefault(key, [])
			tax_components[key].append(component.name)

		return tax_components

	def handle_additional_salary_tax_component(self) -> bool:
		component = next(
			(d for d in self.get("deductions") if d.variable_based_on_taxable_salary and d.additional_salary),
			None,
		)

		if not component:
			return False

		additional_salary = frappe.db.get_value(
			"Additional Salary",
			component.additional_salary,
			["amount", "overwrite_salary_structure_amount"],
			as_dict=1,
		)
		self.additional_salary_amount = additional_salary.amount
		self.additional_salary_component = component.salary_component

		if additional_salary.overwrite_salary_structure_amount:
			return True
		else:
			# overwriting disabled, remove addtional salary tax component
			self.get("deductions", []).remove(component)
			return False

	def calculate_variable_based_on_taxable_salary(self, tax_component):
		if not self.payroll_period:
			frappe.msgprint(
				_("Start and end dates not in a valid Payroll Period, cannot calculate {0}.").format(
					tax_component
				)
			)
			return

		return self.calculate_variable_tax(tax_component)

	def calculate_variable_tax(self, tax_component, has_additional_salary_tax_component=False):
		self.previous_total_paid_taxes = self.get_tax_paid_in_period(
			self.payroll_period.start_date, self.start_date, tax_component
		)

		# Structured tax amount
		eval_locals, default_data = self.get_data_for_eval()
		self.total_structured_tax_amount, __ = calculate_tax_by_tax_slab(
			self.total_taxable_earnings_without_full_tax_addl_components,
			self.tax_slab,
			self.whitelisted_globals,
			eval_locals,
		)

		if has_additional_salary_tax_component:
			self.current_structured_tax_amount = self.additional_salary_amount
		elif self.remaining_sub_periods > 0:
			self.current_structured_tax_amount = (
				self.total_structured_tax_amount - self.previous_total_paid_taxes
			) / self.remaining_sub_periods
		else:
			self.current_structured_tax_amount = 0.0

		# Total taxable earnings with additional earnings with full tax
		self.full_tax_on_additional_earnings = 0.0
		if self.current_additional_earnings_with_full_tax:
			self.total_tax_amount, __ = calculate_tax_by_tax_slab(
				self.total_taxable_earnings, self.tax_slab, self.whitelisted_globals, eval_locals
			)
			self.full_tax_on_additional_earnings = self.total_tax_amount - self.total_structured_tax_amount

		self.current_tax_amount = max(
			0,
			flt(
				self.current_structured_tax_amount
				if has_additional_salary_tax_component
				else (self.current_structured_tax_amount + self.full_tax_on_additional_earnings)
			),
		)

		self._component_based_variable_tax[tax_component].update(
			{
				"previous_total_paid_taxes": self.previous_total_paid_taxes,
				"total_structured_tax_amount": self.total_structured_tax_amount,
				"current_structured_tax_amount": self.current_structured_tax_amount,
				"full_tax_on_additional_earnings": self.full_tax_on_additional_earnings,
				"current_tax_amount": self.current_tax_amount,
			}
		)

	def get_income_tax_slabs(self):
		income_tax_slab = self._salary_structure_assignment.income_tax_slab

		if not income_tax_slab:
			frappe.throw(
				_("Income Tax Slab not set in Salary Structure Assignment: {0}").format(
					get_link_to_form("Salary Structure Assignment", self._salary_structure_assignment.name)
				),
				title=_("Missing Tax Slab"),
			)

		income_tax_slab_doc = frappe.get_cached_doc("Income Tax Slab", income_tax_slab)
		if income_tax_slab_doc.disabled:
			frappe.throw(_("Income Tax Slab: {0} is disabled").format(income_tax_slab))

		if getdate(income_tax_slab_doc.effective_from) > getdate(self.payroll_period.start_date):
			frappe.throw(
				_("Income Tax Slab must be effective on or before Payroll Period Start Date: {0}").format(
					self.payroll_period.start_date
				)
			)

		return income_tax_slab_doc

	def get_tax_paid_in_period(self, start_date, end_date, tax_component):
		# find total_tax_paid, tax paid for benefit, additional_salary
		total_tax_paid = self.get_salary_slip_details(
			start_date,
			end_date,
			parentfield="deductions",
			salary_component=tax_component,
			variable_based_on_taxable_salary=1,
		)

		tax_deducted_till_date = self.get_opening_for("tax_deducted_till_date", start_date, end_date)

		return total_tax_paid + tax_deducted_till_date
