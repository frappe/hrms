# hrms/patches/v1_0/add_attrition_risk_field.py

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def execute():
    """
    Add a custom field 'Attrition Risk' to the Employee doctype.
    """
    if not frappe.db.exists("Custom Field", "Employee-custom_attrition_risk_section"):
        # 1. Create a new Section Break field for better UI organization
        create_custom_field('Employee', {
            "fieldname": "custom_attrition_risk_section",
            "label": "AI Analytics",
            "fieldtype": "Section Break",
            "insert_after": "exit_details_section",  # Find a suitable field to insert after
        })
        print("Created 'AI Analytics' section break in Employee form.")

    if not frappe.db.exists("Custom Field", "Employee-custom_attrition_risk"):
        # 2. Create the HTML field to display the attrition risk
        create_custom_field('Employee', {
            "fieldname": "custom_attrition_risk",
            "label": "Attrition Risk",
            "fieldtype": "HTML",
            "insert_after": "custom_attrition_risk_section",
            "read_only": 1,
            "description": "Predicted employee attrition risk, powered by AI.",
            "options": "<div id='attrition-risk-display' class='control-value'>Loading...</div>"
        })
        print("Created 'Attrition Risk' custom field in Employee form.")
