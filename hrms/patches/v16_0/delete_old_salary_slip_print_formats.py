import frappe
from frappe.model.rename_doc import get_link_fields, update_link_field_values

REPLACEMENTS = {
	"Salary Slip Standard": "Salary Slip Classic",
	"Salary Slip with Year to Date": "Salary Slip Detailed",
	"Salary Slip based on Timesheet": "Salary Slip Classic",
}


def execute():
	link_fields = get_link_fields("Print Format")

	for old, new in REPLACEMENTS.items():
		if not frappe.db.exists("Print Format", {"name": old, "standard": "Yes"}):
			continue

		if frappe.db.exists("Print Format", new):
			update_link_field_values(link_fields, old, new, "Print Format")
			frappe.db.set_value(
				"Property Setter",
				{"doc_type": "Salary Slip", "property": "default_print_format", "value": old},
				"value",
				new,
			)

		frappe.delete_doc("Print Format", old, force=True, ignore_permissions=True)

	frappe.clear_cache(doctype="Salary Slip")
