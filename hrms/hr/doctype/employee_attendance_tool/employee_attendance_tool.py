# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import json
from itertools import zip_longest

import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class EmployeeAttendanceTool(Document):
	pass


@frappe.whitelist()
def get_employees(date, department=None, branch=None, company=None):
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
	)

	marked_employees = {}

	for attendance in attendance_list:
		marked_employees[attendance.employee] = attendance.status

	attendance_unmarked = []
	attendance_marked = []

	for entry in employee_list:
		entry["status"] = marked_employees.get(entry.employee)

		if entry.employee in marked_employees:
			attendance_marked.append(entry)
		else:
			attendance_unmarked.append(entry)

	marked = {
		"Present": [],
		"Absent": [],
		"Half Day": [],
		"Work From Home": [],
	}

	for entry in attendance_list:
		marked.get(entry.status).append(f"{entry.employee} : {entry.employee_name}")

	transposed_marked_attendance = []
	if any(marked.values()):
		# transpose data to fill table with columns as per attendance status
		transposed_marked_attendance = zip_longest(*marked.values(), fillvalue="")

	return {"marked": transposed_marked_attendance, "unmarked": attendance_unmarked}


@frappe.whitelist()
def mark_employee_attendance(
	employee_list,
	status,
	date,
	leave_type=None,
	late_entry=None,
	early_exit=None,
	shift=None,
):
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
