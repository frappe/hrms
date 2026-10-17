from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from hrms.setup import get_custom_fields, rename_employee_details_tab


def execute():
	fields = [
		f for f in get_custom_fields()["Employee"] if f["fieldname"] in ("overview_tab", "overview_html")
	]
	create_custom_fields({"Employee": fields}, ignore_validate=True)
	rename_employee_details_tab()
