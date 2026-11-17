from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from hrms.setup import get_custom_fields, set_employee_form_layout

PROFILE_FIELDS = (
	"profile",
	"employee_profile",
	"profile_sections",
	# placed after the Profile tab now, and before it was first
	"overview_tab",
	"documents_section",
	"documents",
)


def execute():
	fields = [field for field in get_custom_fields()["Employee"] if field["fieldname"] in PROFILE_FIELDS]
	create_custom_fields({"Employee": fields}, ignore_validate=True)
	set_employee_form_layout()
