import frappe


def execute():
	if frappe.db.exists("DocType", "Leave Type"):
		if frappe.db.has_column("Leave Type", "max_days_allowed"):
			frappe.db.sql("alter table `tabLeave Type` drop column max_days_allowed")
