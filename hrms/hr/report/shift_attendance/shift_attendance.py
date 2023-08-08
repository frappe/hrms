# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint, flt


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	report_summary = get_report_summary(data)
	return columns, data, None, chart, report_summary


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


def get_report_summary(data):
	if not data:
		return None
	present_records = half_day_records = absent_records = late_entries = early_exits = 0
	for entry in data:
		if entry.status == "Present":
			present_records += 1
		elif entry.status == "Half Day":
			half_day_records += 1
		else:
			absent_records += 1
		if entry.late_entry:
			late_entries += 1
		if entry.early_exit:
			early_exits += 1
	return [
		{
			"value": present_records,
			"indicator": "Green",
			"label": _("Present Records"),
			"datatype": "Int",
		},
		{
			"value": half_day_records,
			"indicator": "Blue",
			"label": _("Half Day Records"),
			"datatype": "Int",
		},
		{
			"value": absent_records,
			"indicator": "Red",
			"label": _("Absent Records"),
			"datatype": "Int",
		},
		{
			"value": late_entries,
			"indicator": "Red",
			"label": _("Late Entries"),
			"datatype": "Int",
		},
		{
			"value": early_exits,
			"indicator": "Red",
			"label": _("Early Exits"),
			"datatype": "Int",
		},
	]


def get_chart_data(data):
	if not data:
		return None
	total_shift_records = {}
	for entry in data:
		if entry.shift not in total_shift_records:
			total_shift_records[entry.shift] = 0
		total_shift_records[entry.shift] += 1
	labels = [_(d) for d in list(total_shift_records)]
	chart = {
		"data": {
			"labels": labels,
			"datasets": [{"name": _("Shift"), "values": total_shift_records.values()}],
		},
		"type": "donut",
	}
	return chart


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
		d = format_working_hours_precision(d)
		d = format_in_out_time(d)
		d = format_shift_start_end(d)
		d = format_shift_actual_start_end(d)
	return data


def format_working_hours_precision(entry):
	precision = cint(frappe.db.get_default("float_precision")) or 2
	entry.working_hours = flt(entry.working_hours, precision)
	return entry


def format_in_out_time(entry):
	if entry.in_time and not entry.out_time and entry.in_time.date() == entry.attendance_date:
		entry.in_time = entry.in_time.time()
	elif entry.out_time and not entry.in_time and entry.out_time.date() == entry.attendance_date:
		entry.out_time = entry.out_time.time()
	elif entry.in_time and entry.out_time and entry.in_time.date() == entry.out_time.date():
		entry.in_time = entry.in_time.time()
		entry.out_time = entry.out_time.time()
	return entry


def format_shift_start_end(entry):
	if entry.shift_start.date() == entry.shift_end.date():
		entry.shift_start = entry.shift_start.time()
		entry.shift_end = entry.shift_end.time()
	return entry


def format_shift_actual_start_end(entry):
	if entry.shift_actual_start.date() == entry.shift_actual_end.date():
		entry.shift_actual_start = entry.shift_actual_start.time()
		entry.shift_actual_end = entry.shift_actual_end.time()
	return entry
