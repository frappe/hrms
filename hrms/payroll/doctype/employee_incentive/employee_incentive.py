# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document

from hrms.hr.utils import validate_active_employee


class EmployeeIncentive(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		company: DF.Link
		currency: DF.Link
		department: DF.Link | None
		employee: DF.Link
		employee_name: DF.Data | None
		incentive_amount: DF.Currency
		payroll_date: DF.Date
		salary_component: DF.Link
	# end: auto-generated types

	def validate(self):
		validate_active_employee(self.employee)
		self.validate_salary_structure()

	def validate_salary_structure(self):
		if not frappe.db.exists("Salary Structure Assignment", {"employee": self.employee}):
			frappe.throw(
				_("There is no Salary Structure assigned to {0}. First assign a Salary Structure.").format(
					self.employee
				)
			)

	def on_submit(self):
		company = frappe.db.get_value("Employee", self.employee, "company")

		additional_salary = frappe.new_doc("Additional Salary")
		additional_salary.employee = self.employee
		additional_salary.currency = self.currency
		additional_salary.salary_component = self.salary_component
		additional_salary.overwrite_salary_structure_amount = 0
		additional_salary.amount = self.incentive_amount
		additional_salary.payroll_date = self.payroll_date
		additional_salary.company = company
		additional_salary.ref_doctype = self.doctype
		additional_salary.ref_docname = self.name
		additional_salary.submit()
