# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.utils import getdate

from hrms.utils.holiday_list import get_holiday_list_ranges_for_employees, get_holidays_in_ranges_map


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
	employee_filters = {"company": filters.company}
	if filters.department:
		employee_filters["department"] = filters.department

	employees = frappe.get_list("Employee", filters=employee_filters, fields=["name", "company"])
	holiday_list_ranges = get_holiday_list_ranges_for_employees(
		{employee.name: employee.company for employee in employees}, filters.from_date, filters.to_date
	)
	holiday_map = {
		(employee, getdate(holiday.holiday_date)): holiday
		for employee, holidays in get_holidays_in_ranges_map(holiday_list_ranges).items()
		for holiday in holidays
		if not filters.holiday_list or holiday.parent == filters.holiday_list
	}
	if not holiday_map:
		return []

	Attendance = frappe.qb.DocType("Attendance")
	attendance = (
		frappe.qb.from_(Attendance)
		.select(Attendance.employee, Attendance.employee_name, Attendance.attendance_date, Attendance.status)
		.where(Attendance.employee.isin(list({employee for employee, _ in holiday_map})))
		.where(Attendance.attendance_date[filters.from_date : filters.to_date])
		.where(Attendance.status.notin(["Absent", "On Leave"]))
		.where(Attendance.docstatus == 1)
		.orderby(Attendance.employee)
		.orderby(Attendance.attendance_date)
	).run(as_dict=True)

	return [
		[row.employee, row.employee_name, row.attendance_date, row.status, holiday.description]
		for row in attendance
		if (holiday := holiday_map.get((row.employee, getdate(row.attendance_date))))
	]
