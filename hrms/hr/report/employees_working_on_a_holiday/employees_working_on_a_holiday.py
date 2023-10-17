# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_employees(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Employee"),
			"fieldtype": "Link",
			"fieldname": "employee",
			"options": "Employee",
			"width": 120,
		},
		{
			"label": _("Name"),
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("Date"),
			"fieldtype": "Date",
			"width": 100,
		},
		{
			"label": _("Status"),
			"fieldtype": "Data",
			"width": 70,
		},
		{
			"label": _("Holiday"),
			"fieldtype": "Data",
			"width": 200,
		},
	]


def get_employees(filters):
	holiday_filter = [
		["holiday_date", ">=", filters.from_date],
		["holiday_date", "<=", filters.to_date],
	]
	if filters.holiday_list:
		holiday_filter.append(["parent", "=", filters.holiday_list])

	holidays = frappe.get_all("Holiday", fields=["holiday_date", "description"], filters=holiday_filter)

	holiday_names = {}
	holidays_list = []

	for holiday in holidays:
		holidays_list.append(holiday.holiday_date)
		holiday_names[holiday.holiday_date] = holiday.description

	if holidays_list:
		attendance_doctype = frappe.qb.DocType("Attendance")
		employee_list = (
			frappe.qb.from_(attendance_doctype)
			.select(
				attendance_doctype.employee,
				attendance_doctype.employee_name,
				attendance_doctype.attendance_date,
				attendance_doctype.status,
			)
			.where(attendance_doctype.attendance_date.isin(holidays_list))
			.where(attendance_doctype.status.notin(["Absent", "On Leave"]))
		)

		if filters.holiday_list:
			employee = frappe.qb.DocType("Employee")
			employee_based_on_holiday = (
				frappe.qb.from_(employee)
				.select(employee.employee)
				.where(employee.holiday_list == filters.holiday_list)
			)
			employee_list.where(attendance_doctype.employee.isin(employee_based_on_holiday))

		employee_list = employee_list.run(as_list=True)

		for employee_data in employee_list:
			employee_data.append(holiday_names[employee_data[2]])

		return employee_list
	else:
		return []
