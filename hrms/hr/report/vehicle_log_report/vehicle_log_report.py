# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# Monthly Vehicle Log Report - ERPNext Script Report

# Vehicle Log Monthly Report - ERPNext Script Report
# Enhanced Vehicle Log Monthly Report - ERPNext Script Report
import frappe
from frappe.utils import flt
from datetime import date, datetime
from collections import defaultdict

def execute(filters=None):
    columns = [
        {"label": "Month", "fieldname": "month", "fieldtype": "Data", "width": 120},
        {"label": "License Plate", "fieldname": "license_plate", "fieldtype": "Data", "width": 100},
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Data", "width": 150},
        {"label": "Branch", "fieldname": "branch", "fieldtype": "Data", "width": 150},
        {"label": "Designation", "fieldname": "designation", "fieldtype": "Data", "width": 150},
        {"label": "Total KM", "fieldname": "total_km", "fieldtype": "Float", "width": 100},
        {"label": "Fuel Entitled (L)", "fieldname": "fuel_entitled", "fieldtype": "Float", "width": 120},
        {"label": "Fuel Qty (L)", "fieldname": "fuel_qty", "fieldtype": "Float", "width": 100},
        {"label": "Fuel Card Amount", "fieldname": "fuel_card_amount", "fieldtype": "Currency", "width": 120},
        {"label": "Service Expense", "fieldname": "service_total", "fieldtype": "Currency", "width": 120},
        {"label": "Claimable Amount", "fieldname": "claimable_amount", "fieldtype": "Currency", "width": 120},
        {"label": "Grand Total", "fieldname": "grand_total", "fieldtype": "Currency", "width": 120},
    ]

    data = []
    filters = filters or {}

    # Fetch all Vehicle Logs
    logs = frappe.get_all("Vehicle Log",
        fields=[
            "name",
            "license_plate",
            "employee",
            "department",
            "designation",
            "date",
            "total_kms",
            "total_fuel_qty_l",
            "fuel_card_price",
            "fuel_card_entitled_quantity",
            "service_total",
            "amount_to_be_claimed",
            "grand_total_inc_fuel_card"
        ],
        order_by="date asc"
    )

    # Aggregate by Month + Vehicle + Employee
    report_dict = defaultdict(lambda: {
        "total_km": 0,
        "fuel_qty": 0,
        "fuel_entitled": 0,
        "fuel_card_amount": 0,
        "service_total": 0,
        "claimable_amount": 0,
        "grand_total": 0,
        "employee": "",
        "branch": "",
        "designation": ""
    })

    for log in logs:
        # Convert date to Month-Year string
        if isinstance(log['date'], (datetime, date)):
            month = log['date'].strftime("%B %Y")
        else:
            month = datetime.strptime(log['date'], "%Y-%m-%d").strftime("%B %Y")

        key = (month, log['license_plate'], log['employee'])

        report_dict[key]['total_km'] += flt(log['total_kms'])
        report_dict[key]['fuel_qty'] += flt(log['total_fuel_qty_l'])
        report_dict[key]['fuel_entitled'] += flt(log.get('fuel_card_entitled_quantity', 0))
        report_dict[key]['fuel_card_amount'] += flt(log['fuel_card_price'])
        report_dict[key]['service_total'] += flt(log['service_total'])
        report_dict[key]['claimable_amount'] += flt(log['amount_to_be_claimed'])
        report_dict[key]['grand_total'] += flt(log['grand_total_inc_fuel_card'])

        report_dict[key]['employee'] = log.get('employee')
        report_dict[key]['branch'] = log.get('department')
        report_dict[key]['designation'] = log.get('designation')

    # Prepare final data list
    for (month, plate, emp), values in report_dict.items():
        data.append({
            "month": month,
            "license_plate": plate,
            "employee": values['employee'],
            "branch": values['branch'],
            "designation": values['designation'],
            "total_km": values['total_km'],
            "fuel_entitled": values['fuel_entitled'],
            "fuel_qty": values['fuel_qty'],
            "fuel_card_amount": values['fuel_card_amount'],
            "service_total": values['service_total'],
            "claimable_amount": values['claimable_amount'],
            "grand_total": values['grand_total']
        })

    # Add Overall Totals at the end
    if data:
        total_row = {
            "month": "TOTAL",
            "license_plate": "-",
            "employee": "-",
            "branch": "-",
            "designation": "-",
            "total_km": sum(d['total_km'] for d in data),
            "fuel_entitled": sum(d['fuel_entitled'] for d in data),
            "fuel_qty": sum(d['fuel_qty'] for d in data),
            "fuel_card_amount": sum(d['fuel_card_amount'] for d in data),
            "service_total": sum(d['service_total'] for d in data),
            "claimable_amount": sum(d['claimable_amount'] for d in data),
            "grand_total": sum(d['grand_total'] for d in data)
        }
        data.append(total_row)

    return columns, data

