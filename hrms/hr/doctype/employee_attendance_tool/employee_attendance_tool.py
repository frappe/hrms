# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import datetime
import json
import frappe
from frappe.model.document import Document
from frappe.utils import getdate, add_days


class EmployeeAttendanceTool(Document):
    """DocType class for Employee Attendance Tool"""
    pass


# -------------------------------------------------------------------------
# GET EMPLOYEES
# -------------------------------------------------------------------------

@frappe.whitelist()
def get_employees(
    from_date: str | datetime.date,
    to_date: str | datetime.date | None = None,
    department: str | None = None,
    branch: str | None = None,
    company: str | None = None,
    employment_type: str | None = None,
    designation: str | None = None,
    employee_grade: str | None = None,
) -> dict[str, list]:
    """
    Returns marked, half-day marked, and unmarked employees for a date range.
    """
    from_date = getdate(from_date)
    to_date = getdate(to_date) if to_date else from_date

    if to_date < from_date:
        frappe.throw(_("To Date cannot be before From Date."))

    # Filters for active employees
    filters = {"status": "Active", "date_of_joining": ["<=", from_date]}
    optional_filters = {
        "department": department,
        "branch": branch,
        "company": company,
        "employment_type": employment_type,
        "designation": designation,
        "employee_grade": employee_grade,
    }
    for field, value in optional_filters.items():
        if value:
            filters[field] = value

    # All active employees
    employee_list = frappe.get_list(
        "Employee",
        fields=["name as employee", "employee_name"],
        filters=filters,
        order_by="employee_name",
    )

    # Attendance records within the date range
    attendance_list = frappe.get_list(
        "Attendance",
        fields=["employee", "employee_name", "status", "shift", "leave_type", "attendance_date"],
        filters={
            "attendance_date": ["between", [from_date, to_date]],
            "docstatus": 1,
            "modify_half_day_status": 0,
        },
        order_by="employee_name",
    )

    half_day_attendance_list = frappe.get_list(
        "Attendance",
        fields=["employee", "employee_name", "attendance_date"],
        filters={
            "attendance_date": ["between", [from_date, to_date]],
            "docstatus": 1,
            "modify_half_day_status": 1,
            "leave_type": ("is", "set"),
        },
        order_by="employee_name",
    )

    unmarked_attendance = _get_unmarked_attendance(employee_list, attendance_list, from_date, to_date)

    return {
        "marked": attendance_list,
        "half_day_marked": half_day_attendance_list,
        "unmarked": unmarked_attendance,
    }


def _get_unmarked_attendance(employee_list: list, attendance_list: list, from_date, to_date) -> list:
    """
    Returns employees missing attendance on any date in the range.
    """
    # Build a set of (employee, date) that already have attendance
    marked_set = set((att["employee"], att["attendance_date"]) for att in attendance_list)

    unmarked = []
    for emp in employee_list:
        has_missing = False
        for n in range((to_date - from_date).days + 1):
            current_date = add_days(from_date, n)
            if (emp["employee"], current_date) not in marked_set:
                has_missing = True
                break
        if has_missing:
            unmarked.append(emp)

    return unmarked


# -------------------------------------------------------------------------
# MARK ATTENDANCE (DATE RANGE)
# -------------------------------------------------------------------------

@frappe.whitelist()
def mark_employee_attendance(
    employee_list: list | str,
    status: str,
    from_date: str | datetime.date,
    to_date: str | datetime.date | None = None,
    leave_type: str | None = None,
    company: str | None = None,
    late_entry: int | None = None,
    early_exit: int | None = None,
    shift: str | None = None,
    mark_half_day: bool | None = False,
    half_day_status: str | None = None,
    half_day_employee_list: list | str | None = None,
) -> None:
    """
    Marks attendance for employees over a date range.
    Handles full-day and optional half-day marking.
    """
    if isinstance(employee_list, str):
        employee_list = json.loads(employee_list)
    if isinstance(half_day_employee_list, str):
        half_day_employee_list = json.loads(half_day_employee_list)

    if not employee_list and not half_day_employee_list:
        frappe.throw("Please select at least one employee.")

    from_date = getdate(from_date)
    to_date = getdate(to_date) if to_date else from_date

    if to_date < from_date:
        frappe.throw("To Date cannot be before From Date.")

    # -------------------------------
    # Full-day attendance
    # -------------------------------
    for n in range((to_date - from_date).days + 1):
        current_date = add_days(from_date, n)
        for employee in employee_list:
            if frappe.db.exists(
                "Attendance",
                {"employee": employee, "attendance_date": current_date, "docstatus": ["!=", 2]},
            ):
                continue
            attendance = frappe.get_doc(
                {
                    "doctype": "Attendance",
                    "employee": employee,
                    "attendance_date": current_date,
                    "status": status,
                    "leave_type": leave_type if status == "On Leave" else None,
                    "company": company,
                    "late_entry": late_entry,
                    "early_exit": early_exit,
                    "shift": shift,
                }
            )
            attendance.insert()
            attendance.submit()

    # -------------------------------
    # Half-day update
    # -------------------------------
    if mark_half_day and half_day_employee_list:
        for employee in half_day_employee_list:
            attendance_docs = frappe.get_list(
                "Attendance",
                filters={
                    "employee": employee,
                    "attendance_date": ["between", [from_date, to_date]],
                    "docstatus": 1,
                },
                fields=["name"]
            )
            for att in attendance_docs:
                doc = frappe.get_doc("Attendance", att.name)
                doc.half_day_status = half_day_status
                doc.shift = shift
                doc.late_entry = late_entry
                doc.early_exit = early_exit
                doc.modify_half_day_status = 0
                doc.save()

    frappe.msgprint("Attendance marked successfully.")
