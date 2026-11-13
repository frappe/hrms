# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import formatdate, get_link_to_form, getdate

from hrms.hr.utils import get_formatted_value, update_employee_work_history, validate_active_employee


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
		new_salary_structure_assignment: DF.Link | None
		promotion_date: DF.Date
		promotion_details: DF.Table[EmployeePropertyHistory]
		revised_base: DF.Currency
		revised_ctc: DF.Currency
		salary_currency: DF.Link | None
		salary_structure: DF.Link | None
	# end: auto-generated types

	def validate(self):
		validate_active_employee(self.employee)
		self.set_current_salary()
		if self.salary_structure and self.revised_base:
			self.revised_ctc = self.get_revised_ctc()

	def set_current_salary(self):
		salary = get_salary_on(self.employee, self.promotion_date)
		self.current_salary_structure_assignment = salary.name
		self.current_base = salary.base
		self.current_ctc = salary.ctc
		if not self.salary_structure:
			self.salary_structure = salary.salary_structure

	def get_revised_ctc(self) -> float:
		if not (self.salary_structure and self.revised_base):
			return 0.0

		assignment = frappe.new_doc("Salary Structure Assignment")
		assignment.employee = self.get_promoted_employee()
		assignment.salary_structure = self.salary_structure
		assignment.company = self.company
		assignment.currency = frappe.get_cached_value("Salary Structure", self.salary_structure, "currency")
		assignment.from_date = self.promotion_date
		assignment.base = self.revised_base
		if self.current_salary_structure_assignment:
			assignment.variable = frappe.db.get_value(
				"Salary Structure Assignment", self.current_salary_structure_assignment, "variable"
			)

		assignment.calculate_ctc_and_gross()
		return assignment.ctc

	def get_promoted_employee(self) -> Document:
		employee = frappe.get_doc("Employee", self.employee)
		meta = frappe.get_meta("Employee")
		for row in self.promotion_details:
			if field := meta.get_field(row.fieldname):
				employee.set(row.fieldname, get_formatted_value(row.new, field.fieldtype))

		return employee

	def before_submit(self):
		if getdate(self.promotion_date) > getdate():
			frappe.throw(
				_("Employee Promotion cannot be submitted before Promotion Date"),
				frappe.DocstatusTransitionError,
			)

	def validate_no_assignment_from_promotion_date(self):
		existing = frappe.db.get_value(
			"Salary Structure Assignment",
			{"employee": self.employee, "from_date": (">=", self.promotion_date), "docstatus": 1},
			["name", "from_date"],
			as_dict=True,
			order_by="from_date asc",
		)
		if existing:
			frappe.throw(
				_(
					"Salary Structure Assignment {0} starts on {1}, on or after the Promotion Date. Cancel it or change the Promotion Date."
				).format(
					get_link_to_form("Salary Structure Assignment", existing.name),
					formatdate(existing.from_date),
				),
				title=_("Salary Structure Assignment Exists"),
			)

	def on_submit(self):
		employee = frappe.get_doc("Employee", self.employee)
		employee = update_employee_work_history(employee, self.promotion_details, date=self.promotion_date)

		# with a revised base, the CTC changes when HR submits the new Salary Structure Assignment
		if self.revised_ctc and not self.revised_base:
			employee.ctc = self.revised_ctc

		employee.save()

	@frappe.whitelist()
	def make_salary_structure_assignment(self) -> str:
		if self.docstatus != 1:
			frappe.throw(_("Submit the Employee Promotion before creating a Salary Structure Assignment"))
		if not (self.salary_structure and self.revised_base):
			frappe.throw(_("Set the Salary Structure and Revised Base first"))
		# the row lock makes a second click wait for the first, then see its assignment
		existing = frappe.db.get_value(
			"Employee Promotion", self.name, "new_salary_structure_assignment", for_update=True
		)
		if existing:
			frappe.throw(
				_("Salary Structure Assignment {0} is already created for this promotion").format(
					get_link_to_form("Salary Structure Assignment", existing)
				)
			)

		self.validate_no_assignment_from_promotion_date()

		current = frappe._dict()
		if self.current_salary_structure_assignment:
			current = frappe.db.get_value(
				"Salary Structure Assignment",
				self.current_salary_structure_assignment,
				["payroll_payable_account", "income_tax_slab", "variable"],
				as_dict=True,
			)

		assignment = frappe.get_doc(
			{
				"doctype": "Salary Structure Assignment",
				"employee": self.employee,
				"salary_structure": self.salary_structure,
				"company": self.company,
				"currency": frappe.get_cached_value("Salary Structure", self.salary_structure, "currency"),
				"from_date": self.promotion_date,
				"payroll_payable_account": current.payroll_payable_account,
				"base": self.revised_base,
				"variable": current.variable,
				"income_tax_slab": current.income_tax_slab,
			}
		).insert()
		self.db_set("new_salary_structure_assignment", assignment.name)
		return assignment.name

	def on_cancel(self):
		employee = frappe.get_doc("Employee", self.employee)
		employee = update_employee_work_history(employee, self.promotion_details, cancel=True)

		if self.revised_ctc and not self.revised_base:
			employee.ctc = self.current_ctc

		employee.save()
		self.cancel_new_salary_structure_assignment()

	def cancel_new_salary_structure_assignment(self):
		if not self.new_salary_structure_assignment:
			return

		assignment = frappe.get_doc("Salary Structure Assignment", self.new_salary_structure_assignment)
		if assignment.docstatus == 1:
			assignment.cancel()
		elif assignment.docstatus == 0:
			self.db_set("new_salary_structure_assignment", None)
			assignment.delete()


@frappe.whitelist()
def get_current_salary(employee: str, on_date: str) -> frappe._dict:
	frappe.has_permission("Employee", "read", doc=employee, throw=True)

	salary = get_salary_on(employee, on_date)
	if salary.name:
		frappe.has_permission("Salary Structure Assignment", "read", doc=salary.name, throw=True)

	return salary


@frappe.whitelist()
def calculate_revised_ctc(promotion: str | dict) -> float:
	frappe.has_permission("Employee Promotion", "write", throw=True)

	promotion = frappe.parse_json(promotion)
	promotion["doctype"] = "Employee Promotion"
	doc = frappe.get_doc(promotion)

	frappe.has_permission("Employee", "read", doc=doc.employee, throw=True)

	doc.set_current_salary()
	if doc.salary_structure:
		frappe.has_permission("Salary Structure", "read", doc=doc.salary_structure, throw=True)
	if doc.current_salary_structure_assignment:
		frappe.has_permission(
			"Salary Structure Assignment", "read", doc=doc.current_salary_structure_assignment, throw=True
		)

	return doc.get_revised_ctc()


def get_salary_on(employee: str, on_date: str | None) -> frappe._dict:
	assignment = on_date and frappe.db.get_value(
		"Salary Structure Assignment",
		{"employee": employee, "docstatus": 1, "from_date": ("<=", on_date)},
		["name", "salary_structure", "base", "ctc"],
		as_dict=True,
		order_by="from_date desc",
	)
	if assignment:
		return assignment

	return frappe._dict(ctc=frappe.db.get_value("Employee", employee, "ctc"))
