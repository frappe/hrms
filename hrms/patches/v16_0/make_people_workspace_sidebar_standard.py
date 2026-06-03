import frappe


def execute():
	if frappe.db.table_exists("Workspace Sidebar"):
		if frappe.db.exists("Workspace Sidebar", "People"):
			frappe.db.set_value("Workspace Sidebar", "People", "standard", 1)
