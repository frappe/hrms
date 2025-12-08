# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, get_link_to_form, getdate

from hrms.payroll.doctype.payroll_period.payroll_period import get_payroll_period
from hrms.payroll.doctype.salary_structure.salary_structure import validate_max_benefit_for_flexible_benefit


class DuplicateAssignment(frappe.ValidationError):
	pass


class SalaryStructureAssignment(Document):
	def validate(self):
		self.validate_dates()
		self.validate_company()
		self.validate_income_tax_slab()
		self.set_payroll_payable_account()
		validate_max_benefit_for_flexible_benefit(self.employee_benefits, self.max_benefits)

		if not self.get("payroll_cost_centers"):
			self.set_payroll_cost_centers()

		self.validate_cost_centers()
		self.warn_about_missing_opening_entries()

	def on_update_after_submit(self):
		self.validate_cost_centers()

	def validate_dates(self):
		joining_date, relieving_date = frappe.db.get_value(
			"Employee", self.employee, ["date_of_joining", "relieving_date"]
		)

		if self.from_date:
			if frappe.db.exists(
				"Salary Structure Assignment",
				{"employee": self.employee, "from_date": self.from_date, "docstatus": 1},
			):
				frappe.throw(
					_("Salary Structure Assignment for Employee already exists"), DuplicateAssignment
				)

			if joining_date and getdate(self.from_date) < joining_date:
				frappe.throw(
					_("From Date {0} cannot be before employee's joining Date {1}").format(
						self.from_date, joining_date
					)
				)

			# flag - old_employee is for migrating the old employees data via patch
			if relieving_date and getdate(self.from_date) > relieving_date and not self.flags.old_employee:
				frappe.throw(
					_("From Date {0} cannot be after employee's relieving Date {1}").format(
						self.from_date, relieving_date
					)
				)

	def validate_company(self):
		salary_structure_company = frappe.db.get_value(
			"Salary Structure", self.salary_structure, "company", cache=True
		)
		if self.company != salary_structure_company:
			frappe.throw(
				_("Salary Structure {0} does not belong to company {1}").format(
					frappe.bold(self.salary_structure), frappe.bold(self.company)
				)
			)

	def validate_income_tax_slab(self):
		tax_component = get_tax_component(self.salary_structure)
		if tax_component and not self.income_tax_slab:
			frappe.throw(
				_(
					"Income Tax Slab is mandatory since the Salary Structure {0} has a tax component {1}"
				).format(
					get_link_to_form("Salary Structure", self.salary_structure), frappe.bold(tax_component)
				),
				exc=frappe.MandatoryError,
				title=_("Missing Mandatory Field"),
			)

		if not self.income_tax_slab:
			return

		income_tax_slab_currency = frappe.db.get_value("Income Tax Slab", self.income_tax_slab, "currency")
		if self.currency != income_tax_slab_currency:
			frappe.throw(
				_("Currency of selected Income Tax Slab should be {0} instead of {1}").format(
					self.currency, income_tax_slab_currency
				)
			)

	def set_payroll_payable_account(self):
		if not self.payroll_payable_account:
			payroll_payable_account = frappe.db.get_value(
				"Company", self.company, "default_payroll_payable_account"
			)
			if not payroll_payable_account:
				payroll_payable_account = frappe.db.get_value(
					"Account",
					{
						"account_name": _("Payroll Payable"),
						"company": self.company,
						"account_currency": frappe.db.get_value("Company", self.company, "default_currency"),
						"is_group": 0,
					},
				)
			self.payroll_payable_account = payroll_payable_account

	@frappe.whitelist()
	def set_payroll_cost_centers(self):
		self.payroll_cost_centers = []
		default_payroll_cost_center = self.get_payroll_cost_center()
		if default_payroll_cost_center:
			self.append(
				"payroll_cost_centers", {"cost_center": default_payroll_cost_center, "percentage": 100}
			)

	def get_payroll_cost_center(self):
		payroll_cost_center = frappe.db.get_value("Employee", self.employee, "payroll_cost_center")
		if not payroll_cost_center and self.department:
			payroll_cost_center = frappe.db.get_value("Department", self.department, "payroll_cost_center")

		return payroll_cost_center

	def validate_cost_centers(self):
		if not self.get("payroll_cost_centers"):
			return

		total_percentage = 0
		for entry in self.payroll_cost_centers:
			company = frappe.db.get_value("Cost Center", entry.cost_center, "company")
			if company != self.company:
				frappe.throw(
					_("Row {0}: Cost Center {1} does not belong to Company {2}").format(
						entry.idx, frappe.bold(entry.cost_center), frappe.bold(self.company)
					),
					title=_("Invalid Cost Center"),
				)

			total_percentage += flt(entry.percentage)

		if total_percentage != 100:
			frappe.throw(_("Total percentage against cost centers should be 100"))

	def warn_about_missing_opening_entries(self):
		if (
			self.are_opening_entries_required()
			and not self.taxable_earnings_till_date
			and not self.tax_deducted_till_date
		):
			msg = _(
				"Please specify {0} and {1} (if any), for the correct tax calculation in future salary slips."
			).format(
				frappe.bold(_("Taxable Earnings Till Date")),
				frappe.bold(_("Tax Deducted Till Date")),
			)
			frappe.msgprint(
				msg,
				indicator="orange",
				title=_("Missing Opening Entries"),
			)

	@frappe.whitelist()
	def are_opening_entries_required(self) -> bool:
		if not get_tax_component(self.salary_structure):
			return False

		payroll_period = get_payroll_period(self.from_date, self.from_date, self.company)
		if payroll_period and getdate(self.from_date) <= getdate(payroll_period.start_date):
			return False

		return True


def get_assigned_salary_structure(employee, on_date):
	if not employee or not on_date:
		return None

	salary_structure_assignment = frappe.qb.DocType("Salary Structure Assignment")

	query = (
		frappe.qb.from_(salary_structure_assignment)
		.select(salary_structure_assignment.salary_structure)
		.where(salary_structure_assignment.employee == employee)
		.where(salary_structure_assignment.docstatus == 1)
		.where(on_date >= salary_structure_assignment.from_date)
		.orderby(salary_structure_assignment.from_date, order=frappe.qb.desc)
		.limit(1)
	)

	result = query.run()
	return result[0][0] if result else None


@frappe.whitelist()
def get_employee_currency(employee):
	employee_currency = frappe.db.get_value("Salary Structure Assignment", {"employee": employee}, "currency")
	if not employee_currency:
		frappe.throw(
			_("There is no Salary Structure assigned to {0}. First assign a Salary Structure.").format(
				employee
			)
		)
	return employee_currency


def get_tax_component(salary_structure: str) -> str | None:
	salary_structure = frappe.get_cached_doc("Salary Structure", salary_structure)
	for d in salary_structure.deductions:
		if cint(d.variable_based_on_taxable_salary) and not d.formula and not flt(d.amount):
			return d.salary_component
	return None
