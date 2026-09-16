# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _

from hrms.utils.holiday_list import get_holiday_list_ranges_for_employee


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
	Attendance = frappe.qb.DocType("Attendance")
	Holiday = frappe.qb.DocType("Holiday")

	data = []

	employee_filters = {"company": filters.company}
	if filters.department:
		employee_filters["department"] = filters.department

	for employee in frappe.get_list("Employee", filters=employee_filters, pluck="name"):
		for holiday_list_range in get_holiday_list_ranges_for_employee(
			employee, filters.from_date, filters.to_date, raise_exception=False
		):
			if filters.holiday_list and filters.holiday_list != holiday_list_range.holiday_list:
				continue

			working_days = (
				frappe.qb.from_(Attendance)
				.inner_join(Holiday)
				.on(Attendance.attendance_date == Holiday.holiday_date)
				.select(
					Attendance.employee,
					Attendance.employee_name,
					Attendance.attendance_date,
					Attendance.status,
					Holiday.description,
				)
				.where(
					(Attendance.employee == employee)
					& (Attendance.attendance_date[holiday_list_range.from_date : holiday_list_range.to_date])
					& (Attendance.status.notin(["Absent", "On Leave"]))
					& (Attendance.docstatus == 1)
					& (Holiday.parent == holiday_list_range.holiday_list)
				)
				.run(as_list=True)
			)
			data.extend(working_days)

	return data
