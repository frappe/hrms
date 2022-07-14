import frappe


def execute():
	frappe.reload_doc("HR", "doctype", "Leave Allocation")
	frappe.reload_doc("HR", "doctype", "Leave Ledger Entry")
	frappe.db.sql(
		"""
		UPDATE `tabLeave Ledger Entry` as lle
		SET company = (select company from `tabEmployee` where employee = lle.employee)
		WHERE company IS NULL
		"""
	)
	frappe.db.sql(
		"""
		UPDATE `tabLeave Allocation` as la
		SET company = (select company from `tabEmployee` where employee = la.employee)
		WHERE company IS NULL
		"""
	)
