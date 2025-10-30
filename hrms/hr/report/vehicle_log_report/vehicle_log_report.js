// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["VEHICLE LOG REPORT"] = {
    "filters": [
        {
            "fieldname": "employee",
            "label": "Employee Code",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 120
        },
        {
            "fieldname": "branch",
            "label": "Branch",
            "fieldtype": "Link",
            "options": "Branch",
            "width": 120
        },
        {
            "fieldname": "license_plate",
            "label": "Vehicle",
            "fieldtype": "Link",
            "options": "Vehicle Log",
            "width": 120
        },
        {
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "fieldname": "to_date",
            "label": "To Date",
            "fieldtype": "Date",
            "width": 100
        }
    ]
}

