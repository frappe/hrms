# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _, bold
from frappe.model.document import Document
from frappe.utils import comma_and, date_diff, formatdate, get_link_to_form, getdate

from hrms.hr.utils import validate_active_employee


class AdditionalSalary(Document):
	def before_validate(self):
		if self.payroll_date and self.is_recurring:
			self.payroll_date = None

	def on_submit(self):
		self.update_return_amount_in_employee_advance()
		self.update_employee_referral()

	def on_cancel(self):
		self.update_return_amount_in_employee_advance()
		self.update_employee_referral(cancel=True)

	def validate(self):
		validate_active_employee(self.employee)
		self.validate_dates()
		self.validate_salary_structure()
		self.validate_recurring_additional_salary_overlap()
		self.validate_employee_referral()
		self.validate_duplicate_additional_salary()
		self.validate_tax_component_overwrite()

		if self.amount < 0:
			frappe.throw(_("Amount should not be less than zero"))

	def validate_salary_structure(self):
		if not frappe.db.exists("Salary Structure Assignment", {"employee": self.employee}):
			frappe.throw(
				_("There is no Salary Structure assigned to {0}. First assign a Salary Stucture.").format(
					self.employee
				)
			)

	def validate_recurring_additional_salary_overlap(self):
		if self.is_recurring:
			AdditionalSalary = frappe.qb.DocType("Additional Salary")

			additional_salaries = (
				frappe.qb.from_(AdditionalSalary)
				.select(AdditionalSalary.name)
				.where(
					(AdditionalSalary.employee == self.employee)
					& (AdditionalSalary.name != self.name)
					& (AdditionalSalary.docstatus == 1)
					& (AdditionalSalary.is_recurring == 1)
					& (AdditionalSalary.salary_component == self.salary_component)
					& (AdditionalSalary.to_date >= self.from_date)
					& (AdditionalSalary.from_date <= self.to_date)
					& (AdditionalSalary.disabled == 0)
				)
			).run(pluck=True)

			if additional_salaries and len(additional_salaries):
				frappe.throw(
					_(
						"Additional Salary: {0} already exist for Salary Component: {1} for period {2} and {3}"
					).format(
						bold(comma_and(additional_salaries)),
						bold(self.salary_component),
						bold(formatdate(self.from_date)),
						bold(formatdate(self.to_date)),
					)
				)

	def validate_dates(self):
		date_of_joining, relieving_date = frappe.db.get_value(
			"Employee", self.employee, ["date_of_joining", "relieving_date"]
		)

		self.validate_from_to_dates("from_date", "to_date")

		if date_of_joining:
			if self.payroll_date and getdate(self.payroll_date) < getdate(date_of_joining):
				frappe.throw(_("Payroll date can not be less than employee's joining date."))
			elif self.from_date and getdate(self.from_date) < getdate(date_of_joining):
				frappe.throw(_("From date can not be less than employee's joining date."))

		if relieving_date:
			if self.to_date and getdate(self.to_date) > getdate(relieving_date):
				frappe.throw(_("To date can not be greater than employee's relieving date."))
			if self.payroll_date and getdate(self.payroll_date) > getdate(relieving_date):
				frappe.throw(_("Payroll date can not be greater than employee's relieving date."))

	def validate_employee_referral(self):
		if self.ref_doctype == "Employee Referral":
			referral_details = frappe.db.get_value(
				"Employee Referral",
				self.ref_docname,
				["is_applicable_for_referral_bonus", "status"],
				as_dict=1,
			)

			if not referral_details.is_applicable_for_referral_bonus:
				frappe.throw(
					_("Employee Referral {0} is not applicable for referral bonus.").format(self.ref_docname)
				)

			if self.type == "Deduction":
				frappe.throw(_("Earning Salary Component is required for Employee Referral Bonus."))

			if referral_details.status != "Accepted":
				frappe.throw(
					_(
						"Additional Salary for referral bonus can only be created against Employee Referral with status {0}"
					).format(frappe.bold(_("Accepted")))
				)

	def validate_duplicate_additional_salary(self):
		if not self.overwrite_salary_structure_amount:
			return

		AdditionalSalary = frappe.qb.DocType("Additional Salary")
		existing_additional_salary = (
			(
				frappe.qb.from_(AdditionalSalary)
				.select(AdditionalSalary.name)
				.where(
					(AdditionalSalary.name != self.name)
					& (AdditionalSalary.salary_component == self.salary_component)
					& (AdditionalSalary.employee == self.employee)
					& (AdditionalSalary.overwrite_salary_structure_amount == 1)
					& (AdditionalSalary.docstatus == 1)
					& (AdditionalSalary.disabled == 0)
					& (
						(AdditionalSalary.payroll_date == self.payroll_date)
						| (
							(AdditionalSalary.from_date <= self.payroll_date)
							& (AdditionalSalary.to_date >= self.payroll_date)
						)
					)
				)
			)
			.limit(1)
			.run(pluck=True)
		)

		if existing_additional_salary:
			msg = _(
				"Additional Salary for this salary component with {0} enabled already exists for this date"
			).format(frappe.bold(_("Overwrite Salary Structure Amount")))
			msg += "<br><br>"
			msg += _("Reference: {0}").format(
				get_link_to_form("Additional Salary", existing_additional_salary)
			)
			frappe.throw(msg, title=_("Duplicate Overwritten Salary"))

	def validate_tax_component_overwrite(self):
		if not frappe.db.get_value(
			"Salary Component", self.salary_component, "variable_based_on_taxable_salary"
		):
			return

		if self.overwrite_salary_structure_amount:
			frappe.msgprint(
				_(
					"This will overwrite the tax component {0} in the salary slip and tax won't be calculated based on the Income Tax Slabs"
				).format(frappe.bold(self.salary_component)),
				title=_("Warning"),
				indicator="orange",
			)
		else:
			msg = _("{0} has {1} enabled").format(
				get_link_to_form("Salary Component", self.salary_component),
				frappe.bold(_("Variable Based On Taxable Salary")),
			)
			msg += "<br><br>" + _(
				"To overwrite the salary component amount for a tax component, please enable {0}"
			).format(frappe.bold(_("Overwrite Salary Structure Amount")))
			frappe.throw(msg, title=_("Invalid Additional Salary"))

	def update_return_amount_in_employee_advance(self):
		if self.ref_doctype == "Employee Advance" and self.ref_docname:
			return_amount = frappe.db.get_value("Employee Advance", self.ref_docname, "return_amount")

			if self.docstatus == 2:
				return_amount -= self.amount
			else:
				return_amount += self.amount

			frappe.db.set_value("Employee Advance", self.ref_docname, "return_amount", return_amount)
			advance = frappe.get_doc("Employee Advance", self.ref_docname)
			advance.set_status(update=True)

	def update_employee_referral(self, cancel=False):
		if self.ref_doctype == "Employee Referral":
			status = "Unpaid" if cancel else "Paid"
			frappe.db.set_value("Employee Referral", self.ref_docname, "referral_payment_status", status)

	def get_amount(self, sal_start_date, sal_end_date):
		start_date = getdate(sal_start_date)
		end_date = getdate(sal_end_date)
		total_days = date_diff(getdate(self.to_date), getdate(self.from_date)) + 1
		amount_per_day = self.amount / total_days
		if getdate(sal_start_date) <= getdate(self.from_date):
			start_date = getdate(self.from_date)
		if getdate(sal_end_date) > getdate(self.to_date):
			end_date = getdate(self.to_date)
		no_of_days = date_diff(getdate(end_date), getdate(start_date)) + 1
		return amount_per_day * no_of_days

	def validate_update_after_submit(self):
		if not self.disabled:
			self.validate_recurring_additional_salary_overlap()


def get_additional_salaries(employee, start_date, end_date, component_type):
	from frappe.query_builder import Criterion

	comp_type = "Earning" if component_type == "earnings" else "Deduction"

	additional_sal = frappe.qb.DocType("Additional Salary")
	component_field = additional_sal.salary_component.as_("component")
	overwrite_field = additional_sal.overwrite_salary_structure_amount.as_("overwrite")

	additional_salary_list = (
		frappe.qb.from_(additional_sal)
		.select(
			additional_sal.name,
			component_field,
			additional_sal.type,
			additional_sal.amount,
			additional_sal.is_recurring,
			overwrite_field,
			additional_sal.deduct_full_tax_on_selected_payroll_date,
		)
		.where(
			(additional_sal.employee == employee)
			& (additional_sal.docstatus == 1)
			& (additional_sal.type == comp_type)
			& (additional_sal.disabled == 0)
		)
		.where(
			Criterion.any(
				[
					Criterion.all(
						[  # is recurring and additional salary dates fall within the payroll period
							additional_sal.is_recurring == 1,
							additional_sal.from_date <= end_date,
							additional_sal.to_date >= end_date,
						]
					),
					Criterion.all(
						[  # is not recurring and additional salary's payroll date falls within the payroll period
							additional_sal.is_recurring == 0,
							additional_sal.payroll_date[start_date:end_date],
						]
					),
				]
			)
		)
		.run(as_dict=True)
	)

	additional_salaries = []
	components_to_overwrite = []

	for d in additional_salary_list:
		if d.overwrite:
			if d.component in components_to_overwrite:
				frappe.throw(
					_(
						"Multiple Additional Salaries with overwrite property exist for Salary Component {0} between {1} and {2}."
					).format(frappe.bold(d.component), start_date, end_date),
					title=_("Error"),
				)

			components_to_overwrite.append(d.component)

		additional_salaries.append(d)

	return additional_salaries
