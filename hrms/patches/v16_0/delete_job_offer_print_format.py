import frappe


def execute():
	if frappe.db.exists("Print Format", {"name": "Job Offer", "standard": "Yes"}):
		frappe.delete_doc("Print Format", "Job Offer", ignore_permissions=True, force=True)

	frappe.db.delete(
		"Property Setter",
		{"doc_type": "Job Offer", "property": "default_print_format", "value": "Job Offer"},
	)
