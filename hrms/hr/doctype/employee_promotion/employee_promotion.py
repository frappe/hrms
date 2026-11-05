# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from hrms.hr.utils import update_employee_work_history, validate_active_employee


class EmployeePromotion(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.employee_property_history.employee_property_history import (
			EmployeePropertyHistory,
		)

		amended_from: DF.Link | None
		company: DF.Link | None
		current_base: DF.Currency
		current_ctc: DF.Currency
		current_salary_structure_assignment: DF.Link | None
		department: DF.Link | None
		employee: DF.Link
		employee_name: DF.Data | None
		promotion_date: DF.Date
		promotion_details: DF.Table[EmployeePropertyHistory]
		revised_ctc: DF.Currency
		salary_currency: DF.Link | None
		salary_structure: DF.Link | None
	# end: auto-generated types

	def validate(self):
		validate_active_employee(self.employee)
		self.set_current_salary()

	def set_current_salary(self):
		salary = get_salary_on(self.employee, self.promotion_date)
		self.current_salary_structure_assignment = salary.name
		self.current_base = salary.base
		self.current_ctc = salary.ctc
		if not self.salary_structure:
			self.salary_structure = salary.salary_structure

	def before_submit(self):
		if getdate(self.promotion_date) > getdate():
			frappe.throw(
				_("Employee Promotion cannot be submitted before Promotion Date"),
				frappe.DocstatusTransitionError,
			)

	def on_submit(self):
		employee = frappe.get_doc("Employee", self.employee)
		employee = update_employee_work_history(employee, self.promotion_details, date=self.promotion_date)

		if self.revised_ctc:
			employee.ctc = self.revised_ctc

		employee.save()

	def on_cancel(self):
		employee = frappe.get_doc("Employee", self.employee)
		employee = update_employee_work_history(employee, self.promotion_details, cancel=True)

		if self.revised_ctc:
			employee.ctc = self.current_ctc

		employee.save()


@frappe.whitelist()
def get_current_salary(employee: str, on_date: str) -> frappe._dict:
	frappe.has_permission("Employee", "read", doc=employee, throw=True)

	salary = get_salary_on(employee, on_date)
	if salary.name:
		frappe.has_permission("Salary Structure Assignment", "read", doc=salary.name, throw=True)

	return salary


def get_salary_on(employee: str, on_date: str | None) -> frappe._dict:
	assignment = on_date and frappe.db.get_value(
		"Salary Structure Assignment",
		{"employee": employee, "docstatus": 1, "from_date": ("<=", on_date)},
		["name", "salary_structure", "base", "ctc", "currency"],
		as_dict=True,
		order_by="from_date desc",
	)
	if assignment:
		return assignment

	return frappe._dict(ctc=frappe.db.get_value("Employee", employee, "ctc"))
