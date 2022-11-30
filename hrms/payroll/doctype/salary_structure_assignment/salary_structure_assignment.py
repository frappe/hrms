# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class DuplicateAssignment(frappe.ValidationError):
	pass


class SalaryStructureAssignment(Document):
	def onload(self):
		if self.employee:
			res = self.set_earnings_and_taxation_section()
			self.set_onload(
				"unhide_earnings_and_taxation_section", res.get("unhide_earnings_and_taxation_section")
			)

	def validate(self):
		self.validate_dates()
		self.validate_income_tax_slab()
		self.set_payroll_payable_account()

		if self.set_earnings_and_taxation_section().get("unhide_earnings_and_taxation_section"):
			if not self.taxable_earnings_till_date and not self.tax_deducted_till_date:
				frappe.msgprint(
					_(
						"""
						Not found any salary slip record(s) for the employee {0}. <br><br>
						Please specify opening balances for <b>Taxable Earnings Till Date</b> and <b>Tax Deducted Till Date</b> (if any),
						under <b>Earnings and Taxation</b> sections, for the correct tax calculation in future salary slips.
						"""
					).format(self.employee),
					indicator="orange",
					title=_("Warning"),
				)

		if not self.get("payroll_cost_centers"):
			self.set_payroll_cost_centers()

		self.validate_cost_center_distribution()

	def validate_dates(self):
		joining_date, relieving_date = frappe.db.get_value(
			"Employee", self.employee, ["date_of_joining", "relieving_date"]
		)

		if self.from_date:
			if frappe.db.exists(
				"Salary Structure Assignment",
				{"employee": self.employee, "from_date": self.from_date, "docstatus": 1},
			):
				frappe.throw(_("Salary Structure Assignment for Employee already exists"), DuplicateAssignment)

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

	def validate_income_tax_slab(self):
		if not self.income_tax_slab:
			return

		income_tax_slab_currency = frappe.db.get_value(
			"Income Tax Slab", self.income_tax_slab, "currency"
		)
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

	def validate_cost_center_distribution(self):
		if self.get("payroll_cost_centers"):
			total_percentage = sum([flt(d.percentage) for d in self.get("payroll_cost_centers", [])])
			if total_percentage != 100:
				frappe.throw(_("Total percentage against cost centers should be 100"))

	@frappe.whitelist()
	def set_employee_dependent_properties(self):
		self.set_payroll_cost_centers()
		return self.set_earnings_and_taxation_section()

	@frappe.whitelist()
	def set_earnings_and_taxation_section(self):
		if not self.has_joined_in_same_month() or self.has_salary_slip():
			return {
				"unhide_earnings_and_taxation_section": 0,
			}

		return {
			"unhide_earnings_and_taxation_section": 1,
		}

	def has_salary_slip(self):
		"""returns True if salary structure assignment has salary slips else False"""

		salary_slip = frappe.db.get_value(
			"Salary Slip", filters={"employee": self.employee, "docstatus": 1}
		)

		if salary_slip:
			return True

		return False

	def has_joined_in_same_month(self):
		"""returns True if employee joined in same month as salary structure assignment from date else False"""

		date_of_joining = frappe.db.get_value("Employee", self.employee, "date_of_joining")
		from_date = getdate(self.from_date)

		if not self.from_date or not date_of_joining:
			return False

		elif date_of_joining.month == from_date.month:
			return True

		else:
			return False


def get_assigned_salary_structure(employee, on_date):
	if not employee or not on_date:
		return None
	salary_structure = frappe.db.sql(
		"""
		select salary_structure from `tabSalary Structure Assignment`
		where employee=%(employee)s
		and docstatus = 1
		and %(on_date)s >= from_date order by from_date desc limit 1""",
		{
			"employee": employee,
			"on_date": on_date,
		},
	)
	return salary_structure[0][0] if salary_structure else None


@frappe.whitelist()
def get_employee_currency(employee):
	employee_currency = frappe.db.get_value(
		"Salary Structure Assignment", {"employee": employee}, "currency"
	)
	if not employee_currency:
		frappe.throw(
			_("There is no Salary Structure assigned to {0}. First assign a Salary Stucture.").format(
				employee
			)
		)
	return employee_currency
