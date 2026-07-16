import frappe


def execute():
	# Deprecated in favor of the Employee Attendance Tool
	frappe.delete_doc("DocType", "Upload Attendance", ignore_missing=True, force=True)
