import frappe
from frappe.model.utils.rename_field import rename_field


def execute():
	if not frappe.db.table_exists("Identification Document Type") or frappe.db.table_exists(
		"Employee Document Type"
	):
		return

	frappe.rename_doc("DocType", "Identification Document Type", "Employee Document Type", force=True)
	frappe.reload_doc("hr", "doctype", "employee_document_type")
	rename_field("Employee Document Type", "identification_document_type", "document_type")

	# all of them are IDs, and Travel Request offers only the types that have a number
	DocumentType = frappe.qb.DocType("Employee Document Type")
	frappe.qb.update(DocumentType).set(DocumentType.has_number, 1).run()
