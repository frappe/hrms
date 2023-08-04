# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


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
            "width": 150,
        },
        {
            "label": _("Shift"),
            "fieldname": "shift",
            "fieldtype": "Link",
            "width": 150,
        },
        {
            "label": _("Attendance Date"),
            "fieldname": "attendance_date",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "label": _("In Time"),
            "fieldname": "in_time",
            "fieldtype": "Datetime",
            "width": 120,
        },
        {
            "label": _("Out Time"),
            "fieldname": "out_time",
            "fieldtype": "Datetime",
            "width": 120,
        },
        {
            "label": _("Total Working Hours"),
            "fieldname": "working_hours",
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "label": _("Late Entry"),
            "fieldname": "late_entry",
            "fieldtype": "Check",
            "width": 120,
        },
        {
            "label": _("Early Exit"),
            "fieldname": "early_exit",
            "fieldtype": "Check",
            "width": 120,
        },
        {
            "label": _("Department"),
            "fieldname": "department",
            "fieldtype": "Link",
            "width": 120,
        },
        {
            "label": _("Company"),
            "fieldname": "company",
            "fieldtype": "Link",
            "width": 120,
        },
        {
            "label": _("Shift Start Time"),
            "fieldname": "shift_start",
            "fieldtype": "Time",
            "width": 120,
        },
        {
            "label": _("Shift End Time"),
            "fieldname": "shift_end",
            "fieldtype": "Time",
            "width": 120,
        },
        {
            "label": _("Shift Actual Start Time"),
            "fieldname": "shift_actual_start",
            "fieldtype": "Time",
            "width": 120,
        },
        {
            "label": _("Shift Actual End Time"),
            "fieldname": "shift_actual_end",
            "fieldtype": "Time",
            "width": 120,
        },
    ]


def get_data(filters):
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
    )

    return query.run(as_dict=True)
