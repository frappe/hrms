from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from hrms.setup import get_custom_fields


def execute():
	field = next(
		field
		for field in get_custom_fields()["Company"]
		if field["fieldname"] == "default_employee_advance_account"
	)
	create_custom_fields({"Company": [field]})
