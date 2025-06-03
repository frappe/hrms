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
	date: str | datetime.date,
	department: str | None = None,
	branch: str | None = None,
	company: str | None = None,
	employment_type: str | None = None,
	designation: str | None = None,
	employee_grade: str | None = None,
) -> dict[str, list]:
	filters = {"status": "Active", "date_of_joining": ["<=", date]}

	for field, value in {
		"department": department,
		"branch": branch,
		"company": company,
		"employement_type": employment_type,
		"designation": designation,
		"employee_grade": employee_grade,
	}.items():
		if value:
			filters[field] = value
	# list of all employees
	employee_list = frappe.get_list(
		"Employee",
		fields=["employee", "employee_name"],
		filters=filters,
		order_by="employee_name",
	)
	# marked attendance
	attendance_list = frappe.get_list(
		"Attendance",
		fields=["employee", "employee_name", "status", "shift", "leave_type"],
		filters={
			"attendance_date": date,
			"docstatus": 1,
			"modify_half_day_status": 0,
		},
		order_by="employee_name",
	)
	half_day_attendance_list = frappe.get_list(
		"Attendance",
		fields=["employee", "employee_name"],
		filters={
			"attendance_date": date,
			"docstatus": 1,
			"modify_half_day_status": 1,
			"leave_type": ("is", "set"),
		},
		order_by="employee_name",
	)
	unmarked_attendance = _get_unmarked_attendance(
		employee_list, [*attendance_list, *half_day_attendance_list]
	)
	return {
		"marked": attendance_list,
		"half_day_marked": half_day_attendance_list,
		"unmarked": unmarked_attendance,
	}


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
	leave_type: str | None = None,
	company: str | None = None,
	late_entry: int | None = None,
	early_exit: int | None = None,
	shift: str | None = None,
	mark_half_day: bool | None = False,
	half_day_status: str | None = None,
	half_day_employee_list: list | str | None = None,
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
	if mark_half_day:
		if isinstance(half_day_employee_list, str):
			half_day_employee_list = json.loads(half_day_employee_list)
		Attendance = frappe.qb.DocType("Attendance")
		for employee in half_day_employee_list:
			frappe.qb.update(Attendance).where(
				(Attendance.employee == employee) & (Attendance.attendance_date == date)
			).set(Attendance.half_day_status, half_day_status).set(Attendance.shift, shift).set(
				Attendance.late_entry, late_entry
			).set(Attendance.early_exit, early_exit).set(Attendance.modify_half_day_status, 0).run()
