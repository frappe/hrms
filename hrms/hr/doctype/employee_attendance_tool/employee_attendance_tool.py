# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import datetime
import json

import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class EmployeeAttendanceTool(Document):
	pass


@frappe.whitelist()
def get_employees(
	date: str | datetime.date, department: str = None, branch: str = None, company: str = None
) -> dict[str, list]:
	filters = {"status": "Active", "date_of_joining": ["<=", date]}

	for field, value in {"department": department, "branch": branch, "company": company}.items():
		if value:
			filters[field] = value

	employee_list = frappe.get_list(
		"Employee", fields=["employee", "employee_name"], filters=filters, order_by="employee_name"
	)
	attendance_list = frappe.get_list(
		"Attendance",
		fields=["employee", "employee_name", "status"],
		filters={
			"attendance_date": date,
			"docstatus": 1,
		},
		order_by="employee_name",
	)

	unmarked_attendance = _get_unmarked_attendance(employee_list, attendance_list)

	return {"marked": attendance_list, "unmarked": unmarked_attendance}


def _get_unmarked_attendance(employee_list: list[dict], attendance_list: list[dict]) -> list[dict]:
	marked_employees = [entry.employee for entry in attendance_list]
	unmarked_attendance = []

	for entry in employee_list:
		if entry.employee not in marked_employees:
			unmarked_attendance.append(entry)

	return unmarked_attendance


@frappe.whitelist()
def mark_employee_attendance(
	employee_list: list | str,
	status: str,
	date: str | datetime.date,
	leave_type: str = None,
	company: str = None,
	late_entry: int = None,
	early_exit: int = None,
	shift: str = None,
) -> None:
	if isinstance(employee_list, str):
		employee_list = json.loads(employee_list)

	for employee in employee_list:
		leave_type = None
		if status == "On Leave" and leave_type:
			leave_type = leave_type

		attendance = frappe.get_doc(
			dict(
				doctype="Attendance",
				employee=employee,
				attendance_date=getdate(date),
				status=status,
				leave_type=leave_type,
				late_entry=late_entry,
				early_exit=early_exit,
				shift=shift,
			)
		)
		attendance.insert()
		attendance.submit()
