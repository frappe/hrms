# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _

from hrms.utils.holiday_list import get_holiday_records_between_range


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Employee"),
			"fieldtype": "Link",
			"fieldname": "employee",
			"options": "Employee",
			"width": 300,
		},
		{
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 0,
			"hidden": 1,
		},
		{
			"label": _("Date"),
			"fieldtype": "Date",
			"width": 120,
		},
		{
			"label": _("Status"),
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": _("Holiday"),
			"fieldtype": "Data",
			"width": 200,
		},
	]


def get_data(filters):
	data = []

	employee_filters = {"company": filters.company}
	if filters.department:
		employee_filters["department"] = filters.department

	for employee in frappe.get_list("Employee", filters=employee_filters, pluck="name"):
		holiday_map = {
			holiday.holiday_date: holiday.description
			for holiday in get_holiday_records_between_range(
				employee,
				filters.from_date,
				filters.to_date,
				fields=["parent", "holiday_date", "description"],
				raise_exception_for_holiday_list=False,
			)
			if not filters.holiday_list or holiday.parent == filters.holiday_list
		}
		if not holiday_map:
			continue

		working_days = [
			(
				attendance.employee,
				attendance.employee_name,
				attendance.attendance_date,
				attendance.status,
				holiday_map[attendance.attendance_date],
			)
			for attendance in frappe.get_all(
				"Attendance",
				filters={
					"employee": employee,
					"attendance_date": ("between", [filters.from_date, filters.to_date]),
					"status": ("not in", ["Absent", "On Leave"]),
					"docstatus": 1,
				},
				fields=["employee", "employee_name", "attendance_date", "status"],
			)
			if attendance.attendance_date in holiday_map
		]
		data.extend(working_days)

	return data
