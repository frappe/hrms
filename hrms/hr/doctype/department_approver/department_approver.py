# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder import Order
from frappe.utils import get_link_to_form


class DepartmentApprover(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		approver: DF.Link
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
	# end: auto-generated types

	pass


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_approvers(doctype: str, txt: str, searchfield: str, start: int, page_len: int, filters: dict):
	if not filters.get("employee"):
		frappe.throw(_("Please select Employee first."))

	approvers = []
	department_details = {}
	department_list = []
	employee = frappe.get_value(
		"Employee",
		filters.get("employee"),
		["employee_name", "department", "leave_approver", "expense_approver", "shift_request_approver"],
		as_dict=True,
	)

	employee_department = filters.get("department") or employee.department
	if employee_department:
		department_details = frappe.db.get_value(
			"Department", {"name": employee_department}, ["lft", "rgt"], as_dict=True
		)
	if department_details:
		Department = frappe.qb.DocType("Department")
		department_list = (
			frappe.qb.from_(Department)
			.select(Department.name)
			.where(
				(Department.lft <= department_details.lft)
				& (Department.rgt >= department_details.rgt)
				& (Department.disabled == 0)
			)
			.orderby(Department.lft, order=Order.desc)
		).run(as_list=True)

	if filters.get("doctype") == "Leave Application" and employee.leave_approver:
		approvers.append(
			frappe.db.get_value("User", employee.leave_approver, ["name", "first_name", "last_name"])
		)

	if filters.get("doctype") == "Expense Claim" and employee.expense_approver:
		approvers.append(
			frappe.db.get_value("User", employee.expense_approver, ["name", "first_name", "last_name"])
		)

	if filters.get("doctype") == "Shift Request" and employee.shift_request_approver:
		approvers.append(
			frappe.db.get_value("User", employee.shift_request_approver, ["name", "first_name", "last_name"])
		)

	if filters.get("doctype") == "Leave Application":
		parentfield = "leave_approvers"
		field_name = "Leave Approver"
	elif filters.get("doctype") == "Expense Claim":
		parentfield = "expense_approvers"
		field_name = "Expense Approver"
	elif filters.get("doctype") == "Shift Request":
		parentfield = "shift_request_approver"
		field_name = "Shift Request Approver"
	if department_list:
		User = frappe.qb.DocType("User")
		Approver = frappe.qb.DocType("Department Approver")
		for d in department_list:
			approvers += (
				frappe.qb.from_(User)
				.from_(Approver)
				.select(User.name, User.first_name, User.last_name)
				.where(
					(Approver.parent == d)
					& (User.name.like("%" + txt + "%"))
					& (Approver.parentfield == parentfield)
					& (Approver.approver == User.name)
				)
			).run(as_list=True)

	if len(approvers) == 0:
		error_msg = _("Please set {0} for the Employee: {1}").format(
			frappe.bold(_(field_name)),
			get_link_to_form("Employee", filters.get("employee"), employee.employee_name),
		)
		if department_list:
			error_msg += " " + _("or for the Employee's Department: {0}").format(
				get_link_to_form("Department", employee_department)
			)
		frappe.throw(error_msg, title=_("{0} Missing").format(_(field_name)))

	return set(tuple(approver) for approver in approvers)
