# hrms/hr/report/employee_data_integrity_report/employee_data_integrity_report.py

import frappe
from frappe.utils import getdate

def execute(filters=None):
    columns = get_columns()
    data = []

    # Get all active employees
    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "employee_name", "date_of_birth", "date_of_joining", "relieving_date", "department", "designation"]
    )

    for emp in employees:
        # Rule 1: Active employees should not have a relieving date.
        if emp.relieving_date:
            data.append({
                "employee": emp.name,
                "employee_name": emp.employee_name,
                "issue": "Active employee has a relieving date set."
            })

        # Rule 2: Date of joining must be after date of birth.
        if emp.date_of_joining and emp.date_of_birth and getdate(emp.date_of_joining) <= getdate(emp.date_of_birth):
            data.append({
                "employee": emp.name,
                "employee_name": emp.employee_name,
                "issue": "Date of Joining is on or before the Date of Birth."
            })

        # Rule 3: Department and Designation should be set.
        if not emp.department:
            data.append({
                "employee": emp.name,
                "employee_name": emp.employee_name,
                "issue": "Department is not set for this active employee."
            })
        if not emp.designation:
            data.append({
                "employee": emp.name,
                "employee_name": emp.employee_name,
                "issue": "Designation is not set for this active employee."
            })

    return columns, data

def get_columns():
    return [
        {
            "label": "Employee",
            "fieldname": "employee",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 150
        },
        {
            "label": "Employee Name",
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": "Issue Found",
            "fieldname": "issue",
            "fieldtype": "Data",
            "width": 400
        }
    ]
