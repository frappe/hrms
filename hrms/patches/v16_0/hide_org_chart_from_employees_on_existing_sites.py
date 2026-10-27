import frappe


def execute():
	# keep the directory off on existing sites until HR turns it on
	frappe.db.set_single_value("HR Settings", "show_org_chart_to_all_employees", 0)
