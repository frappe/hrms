import frappe


def execute():
	"""
	Add `Expense Claim` to Repost settings
	"""
	allowed_types = ["Expense Claim"]
	repost_settings = frappe.get_doc("Repost Accounting Ledger Settings")
	for x in allowed_types:
		repost_settings.append("allowed_types", {"document_type": x, "allowed": True})
	repost_settings.save()
