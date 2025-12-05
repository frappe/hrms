import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields(
        {
            "Employee Checkin": [
                {
                    "fieldname": "location",
                    "label": "Location",
                    "fieldtype": "Link",
                    "options": "Location",
                    "insert_after": "latitude",
                },
                {
                    "fieldname": "description",
                    "fieldtype": "Data",
                    "label": "Description",
                    "read_only": 1,
                    "insert_after": "longitude",
                },
                {
                    "fieldname": "section_break_qljs",
                    "fieldtype": "Section Break",
                    "insert_after": "shift_actual_end",
                },
                {
                    "fieldname": "reference_dt",
                    "fieldtype": "Link",
                    "in_list_view": 1,
                    "label": "Reference ",
                    "options": "DocType",
                    "read_only": 1,
                    "insert_after": "section_break_qljs",
                },
                {
                    "fieldname": "column_break_ipbc",
                    "fieldtype": "Column Break",
                    "insert_after": "reference_dt",
                },
                {
                    "fieldname": "reference_dn",
                    "fieldtype": "Dynamic Link",
                    "in_list_view": 1,
                    "label": "Reference Name",
                    "options": "reference_dt",
                    "read_only": 1,
                    "insert_after": "column_break_ipbc",
                },
            ],
            "User": [
                {
                    "collapsible": 1,
                    "fieldname": "expense_claim_allowance_section",
                    "fieldtype": "Section Break",
                    "label": "Expense Claim Allowance",
                    "insert_after": "onboarding_status",
                },
                {
                    "fieldname": "vehicle_type",
                    "fieldtype": "Select",
                    "label": "Vehicle Type ",
                    "options": "\nBike\nCar\nBoth",
                    "insert_after": "expense_claim_allowance_section",
                },
            ],
            "Employee":[
                {
                    "fieldname": "field_employee",
                    "fieldtype": "Select",
                    "label": "Field Employee",
                    "options": "\nYes\nNo",
                    "reqd": 1,
                    "insert_after": "attendance_device_id",
                }
            ]
        }
    )