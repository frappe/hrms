# hrms/patches/v1_0/add_career_path_field.py

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def execute():
    """
    Add a custom section and field for 'Career Path' to the Employee doctype.
    """
    if not frappe.db.exists("Custom Field", "Employee-custom_career_path_section"):
        create_custom_field('Employee', {
            "fieldname": "custom_career_path_section",
            "label": "Career Development",
            "fieldtype": "Section Break",
            "insert_after": "custom_attrition_risk",
        })
        print("Created 'Career Development' section break in Employee form.")

    if not frappe.db.exists("Custom Field", "Employee-custom_career_path_suggestions"):
        create_custom_field('Employee', {
            "fieldname": "custom_career_path_suggestions",
            "label": "Career Path Suggestions",
            "fieldtype": "HTML",
            "insert_after": "custom_career_path_section",
            "read_only": 1,
        })
        print("Created 'Career Path Suggestions' custom field in Employee form.")
