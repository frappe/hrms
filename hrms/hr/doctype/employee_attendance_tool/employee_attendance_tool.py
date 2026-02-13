# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import datetime
import json

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, add_days


class EmployeeAttendanceTool(Document):
    pass


# -------------------------------------------------------------------------
# GET EMPLOYEES
# -------------------------------------------------------------------------

@frappe.whitelist()
def get_employees(
    from_date: str | datetime.date,
    department: str | None = None,
    branch: str | None = None,
    company: str | None = None,
    employment_type: str | None = None,
    designation: str | None = None,
    employee_grade: str | None = None,
) -> dict[str, list]:

    from_date = getdate(from_date)

    filters = {
        "status": "Active",
        "date_of_joining": ["<=", from_date],
    }

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

    # All employees
    employee_list = frappe.get_list(
        "Employee",
        fields=["name as employee", "employee_name"],
        filters=filters,
        order_by="employee_name",
    )

    # Marked attendance
    attendance_list = frappe.get_list(
        "Attendance",
        fields=["employee", "employee_name", "status", "shift", "leave_type"],
        filters={
            "attendance_date": from_date,
            "docstatus": 1,
            "modify_half_day_status": 0,
        },
        order_by="employee_name",
    )

    # Half day attendance
    half_day_attendance_list = frappe.get_list(
        "Attendance",
        fields=["employee", "employee_name"],
        filters={
            "attendance_date": from_date,
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
    """Return employees who don’t have attendance marked yet"""
    marked_employees = [entry.get("employee") for entry in attendance_list]

    return [
        employee
        for employee in employee_list
        if employee.get("employee") not in marked_employees
    ]


# -------------------------------------------------------------------------
# MARK ATTENDANCE (SINGLE DATE OR DATE RANGE)
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

    # Convert JSON strings to lists if needed
    if isinstance(employee_list, str):
        employee_list = json.loads(employee_list)

    if isinstance(half_day_employee_list, str):
        half_day_employee_list = json.loads(half_day_employee_list)

    if not employee_list:
        frappe.throw("Please select at least one employee.")

    # Convert to datetime
    from_date = getdate(from_date)
    to_date = getdate(to_date) if to_date else from_date

    # Validate date range
    if to_date < from_date:
        frappe.throw("To Date cannot be before From Date.")

    current_date = from_date

    while current_date <= to_date:

        for employee in employee_list:

            # Skip if attendance already exists
            if frappe.db.exists(
                "Attendance",
                {
                    "employee": employee,
                    "attendance_date": current_date,
                    "docstatus": ["!=", 2],
                },
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

        current_date = add_days(current_date, 1)

    # -----------------------------------------------------------------
    # HALF DAY UPDATE (OPTIONAL)
    # -----------------------------------------------------------------

    if mark_half_day and half_day_employee_list:

        Attendance = frappe.qb.DocType("Attendance")

        for employee in half_day_employee_list:
            frappe.qb.update(Attendance).where(
                (Attendance.employee == employee)
                & (Attendance.attendance_date >= from_date)
                & (Attendance.attendance_date <= to_date)
            ).set(
                Attendance.half_day_status, half_day_status
            ).set(
                Attendance.shift, shift
            ).set(
                Attendance.late_entry, late_entry
            ).set(
                Attendance.early_exit, early_exit
            ).set(
                Attendance.modify_half_day_status, 0
            ).run()

    frappe.msgprint("Attendance marked successfully.")
