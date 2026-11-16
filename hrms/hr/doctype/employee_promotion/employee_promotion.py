# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import formatdate, get_link_to_form, getdate

from hrms.hr.utils import get_formatted_value, update_employee_work_history, validate_active_employee
from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import (
	PERIODS_PER_YEAR,
	get_promotion_assignments,
)
from hrms.payroll.utils import get_breakup_rows


class EmployeePromotion(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.employee_property_history.employee_property_history import (
			EmployeePropertyHistory,
		)
		from hrms.hr.doctype.job_offer_component.job_offer_component import JobOfferComponent

		amended_from: DF.Link | None
		company: DF.Link | None
		ctc_breakup: DF.Table[JobOfferComponent]
		current_base: DF.Currency
		current_ctc: DF.Currency
		current_salary_structure: DF.Link | None
		current_salary_structure_assignment: DF.Link | None
		department: DF.Link | None
		employee: DF.Link
		employee_name: DF.Data | None
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
		self.set_revised_salary()

	def set_current_salary(self):
		salary = get_salary_on(self.employee, self.promotion_date)
		self.current_salary_structure_assignment = salary.name
		self.current_salary_structure = salary.salary_structure
		self.current_base = salary.base
		self.current_ctc = salary.ctc
		if not self.salary_structure:
			self.salary_structure = salary.salary_structure

	def set_revised_salary(self):
		self.set("ctc_breakup", [])
		assignment = self.get_revised_assignment()
		if not assignment:
			return

		self.revised_ctc = assignment.ctc
		frequency = frappe.get_cached_value("Salary Structure", self.salary_structure, "payroll_frequency")
		periods = PERIODS_PER_YEAR.get(frequency, 12)
		self.set("ctc_breakup", get_breakup_rows(assignment, periods, assignment.ctc))

	def get_revised_ctc(self) -> float:
		assignment = self.get_revised_assignment()
		return assignment.ctc if assignment else 0.0

	def get_revised_assignment(self) -> Document | None:
		if not (self.salary_structure and self.revised_base):
			return None

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
		return assignment

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

		if self.revised_ctc:
			employee.ctc = self.revised_ctc

		employee.save()

	def onload(self):
		self.set_onload("salary_structure_assignment", self.get_salary_structure_assignment())

	def get_salary_structure_assignment(self) -> frappe._dict | None:
		if self.is_new():
			return None
		assignments = get_promotion_assignments(self.name)
		return assignments[0] if assignments else None

	def validate_can_create_salary_structure_assignment(self):
		if self.docstatus != 1:
			frappe.throw(_("Submit the Employee Promotion before creating a Salary Structure Assignment"))
		if not (self.salary_structure and self.revised_base):
			frappe.throw(_("Set the Salary Structure and Revised Base first"))
		if existing := self.get_salary_structure_assignment():
			frappe.throw(
				_("Salary Structure Assignment {0} is already created for this promotion").format(
					get_link_to_form("Salary Structure Assignment", existing.name)
				),
				title=_("Salary Structure Assignment Exists"),
			)

		self.validate_no_assignment_from_promotion_date()

	def on_cancel(self):
		employee = frappe.get_doc("Employee", self.employee)
		employee = update_employee_work_history(employee, self.promotion_details, cancel=True)

		if self.revised_ctc:
			employee.ctc = self.current_ctc

		employee.save()
		self.cancel_salary_structure_assignments()

	def cancel_salary_structure_assignments(self):
		for assignment in get_promotion_assignments(self.name):
			if assignment.docstatus == 1:
				frappe.get_doc("Salary Structure Assignment", assignment.name).cancel()
			else:
				frappe.delete_doc("Salary Structure Assignment", assignment.name)


@frappe.whitelist()
def make_salary_structure_assignment(source_name: str) -> Document:
	frappe.has_permission("Salary Structure Assignment", "create", throw=True)
	promotion = frappe.get_doc("Employee Promotion", source_name)
	promotion.check_permission("read")
	promotion.validate_can_create_salary_structure_assignment()

	# the form shows these before the first save, when fetch_from has not run yet
	employee = frappe.db.get_value(
		"Employee", promotion.employee, ["employee_name", "department", "designation", "grade"], as_dict=True
	)

	current = frappe._dict()
	if promotion.current_salary_structure_assignment:
		current = frappe.db.get_value(
			"Salary Structure Assignment",
			promotion.current_salary_structure_assignment,
			["payroll_payable_account", "income_tax_slab", "variable"],
			as_dict=True,
		)

	assignment = frappe.new_doc("Salary Structure Assignment")
	assignment.update(
		{
			"employee": promotion.employee,
			**employee,
			"employee_promotion": promotion.name,
			"salary_structure": promotion.salary_structure,
			"company": promotion.company,
			"currency": frappe.get_cached_value("Salary Structure", promotion.salary_structure, "currency"),
			"from_date": promotion.promotion_date,
			"payroll_payable_account": current.payroll_payable_account,
			"base": promotion.revised_base,
			"variable": current.variable,
			"income_tax_slab": current.income_tax_slab,
		}
	)
	return assignment


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
