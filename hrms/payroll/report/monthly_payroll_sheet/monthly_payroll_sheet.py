# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe

import frappe
from frappe.utils import flt

def execute(filters=None):
    if not filters:
        filters = {}

    # Get all employees
    employees = frappe.get_all("Employee", fields=[
        "name", "employee_name", "branch", "department", "designation", "date_of_joining"
    ])

    data = []

    for emp in employees:
        # Get Salary Slip for the employee within date range
        salary_slip = frappe.get_all("Salary Slip",
            filters={
                "employee": emp.name,
                "docstatus": 1,
                "start_date": ["<=", filters.get("to_date")],
                "end_date": [">=", filters.get("from_date")]
            },
            fields=[
                "gross_pay",
                "total_deduction",
                "net_pay"
            ],
            limit=1
        )

        if salary_slip:
            ss = salary_slip[0]
            data.append({
                "employee": emp.name,
                "employee_name": emp.employee_name,
                "branch": emp.branch,
                "department": emp.department,
                "designation": emp.designation,
                "data_of_joining": emp.date_of_joining,
                "gross_monthly_salary": flt(ss.gross_pay),
                "gross_pay": flt(ss.gross_pay),
                "total_deduction": flt(ss.total_deduction),
                "net_pay": flt(ss.net_pay)
            })
        else:
            # If no salary slip exists in the period, return zero values
            data.append({
                "employee": emp.name,
                "employee_name": emp.employee_name,
                "branch": emp.branch,
                "department": emp.department,
                "designation": emp.designation,
                "data_of_joining": emp.date_of_joining,
                "gross_monthly_salary": 0,
                "gross_pay": 0,
                "total_deduction": 0,
                "net_pay": 0
            })

    # Define report columns
    columns = [
        {"label":"Employee","fieldname":"employee","fieldtype":"Link","options":"Employee","width":200},
        {"label":"Employee Name","fieldname":"employee_name","fieldtype":"Data","width":140},
        {"label":"Branch","fieldname":"branch","fieldtype":"Link","options":"Branch","width":120},
        {"label":"Department","fieldname":"department","fieldtype":"Link","options":"Department","width":120},
        {"label":"Designation","fieldname":"designation","fieldtype":"Link","options":"Designation","width":120},
        {"label":"Date of Joining","fieldname":"data_of_joining","fieldtype":"Date","width":120},
        {"label":"Standard Gross Salary","fieldname":"gross_monthly_salary","fieldtype":"Currency","width":120},
        {"label":"Gross Payable","fieldname":"gross_pay","fieldtype":"Currency","width":120},
        {"label":"Total Deduction","fieldname":"total_deduction","fieldtype":"Currency","width":120},
        {"label":"Net Payable","fieldname":"net_pay","fieldtype":"Currency","width":120},
    ]

    return columns, data
