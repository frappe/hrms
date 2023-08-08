# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint, flt


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120,
		},
		{
			"label": _("Shift"),
			"fieldname": "shift",
			"fieldtype": "Link",
			"options": "Shift Type",
			"width": 100,
		},
		{
			"label": _("Attendance Date"),
			"fieldname": "attendance_date",
			"fieldtype": "Date",
			"width": 120,
		},
		{
			"label": _("Attendance Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("In Time"),
			"fieldname": "in_time",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Out Time"),
			"fieldname": "out_time",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Total Working Hours"),
			"fieldname": "working_hours",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": _("Late Entry"),
			"fieldname": "late_entry",
			"fieldtype": "Check",
			"width": 80,
		},
		{
			"label": _("Early Exit"),
			"fieldname": "early_exit",
			"fieldtype": "Check",
			"width": 80,
		},
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 150,
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 150,
		},
		{
			"label": _("Shift Start Time"),
			"fieldname": "shift_start",
			"fieldtype": "Data",
			"width": 125,
		},
		{
			"label": _("Shift End Time"),
			"fieldname": "shift_end",
			"fieldtype": "Data",
			"width": 125,
		},
		{
			"label": _("Shift Actual Start Time"),
			"fieldname": "shift_actual_start",
			"fieldtype": "Data",
			"width": 165,
		},
		{
			"label": _("Shift Actual End Time"),
			"fieldname": "shift_actual_end",
			"fieldtype": "Data",
			"width": 165,
		},
	]


def get_data(filters):
	query = get_query(filters)
	data = query.run(as_dict=True)
	data = format_data(data)
	return data


def get_query(filters):
	attendance = frappe.qb.DocType("Attendance")
	checkin = frappe.qb.DocType("Employee Checkin")
	query = (
		frappe.qb.from_(attendance)
		.inner_join(checkin)
		.on(checkin.attendance == attendance.name)
		.select(
			attendance.employee,
			attendance.shift,
			attendance.attendance_date,
			attendance.status,
			attendance.in_time,
			attendance.out_time,
			attendance.working_hours,
			attendance.late_entry,
			attendance.early_exit,
			attendance.department,
			attendance.company,
			checkin.shift_start,
			checkin.shift_end,
			checkin.shift_actual_start,
			checkin.shift_actual_end,
		)
		.groupby(attendance.name)
		.where(attendance.docstatus == 1)
	)
	for filter in filters:
		if filter == "from_date":
			query = query.where(attendance.attendance_date >= filters.from_date)
		elif filter == "to_date":
			query = query.where(attendance.attendance_date <= filters.to_date)
		else:
			query = query.where(attendance[filter] == filters[filter])
	return query


def format_data(data):
	for d in data:
		precision = cint(frappe.db.get_default("float_precision")) or 2
		d.working_hours = flt(d.working_hours, precision)
		if d.in_time.date() == d.out_time.date():
			d.in_time = d.in_time.time()
			d.out_time = d.out_time.time()
		if d.shift_start.date() == d.shift_end.date():
			d.shift_start = d.shift_start.time()
			d.shift_end = d.shift_end.time()
		if d.shift_actual_start.date() == d.shift_actual_end.date():
			d.shift_actual_start = d.shift_actual_start.time()
			d.shift_actual_end = d.shift_actual_end.time()
	return data
