from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_field


def execute():
	create_custom_field(
		"Employee",
		{
			"fieldname": "employee_advance_account",
			"fieldtype": "Link",
			"label": _("Employee Advance Account"),
			"options": "Account",
			"insert_after": "salary_mode",
		},
	)
