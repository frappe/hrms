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
		d = format_working_ours_precision(d)
		d = format_in_out_time(d)
		d = format_shift_start_end(d)
		d = format_shift_actual_start_end(d)
	return data


def format_working_ours_precision(record):
	precision = cint(frappe.db.get_default("float_precision")) or 2
	record.working_hours = flt(record.working_hours, precision)
	return record


def format_in_out_time(record):
	if record.in_time and not record.out_time and record.in_time.date() == record.attendance_date:
		record.in_time = record.in_time.time()
	elif record.out_time and not record.in_time and record.out_time.date() == record.attendance_date:
		record.out_time = record.out_time.time()
	elif record.in_time and record.out_time and record.in_time.date() == record.out_time.date():
		record.in_time = record.in_time.time()
		record.out_time = record.out_time.time()
	return record


def format_shift_start_end(record):
	if record.shift_start.date() == record.shift_end.date():
		record.shift_start = record.shift_start.time()
		record.shift_end = record.shift_end.time()
	return record


def format_shift_actual_start_end(record):
	if record.shift_actual_start.date() == record.shift_actual_end.date():
		record.shift_actual_start = record.shift_actual_start.time()
		record.shift_actual_end = record.shift_actual_end.time()
	return record
