import frappe


def execute():
	# Deprecated: Daily Work Summary, its group doctypes, the Team Updates page and replies report
	frappe.delete_doc("Report", "Daily Work Summary Replies", ignore_missing=True, force=True)
	frappe.delete_doc("Page", "team-updates", ignore_missing=True, force=True)

	for doctype in ("Daily Work Summary", "Daily Work Summary Group", "Daily Work Summary Group User"):
		frappe.delete_doc("DocType", doctype, ignore_missing=True, force=True)
