from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	custom_fields = {
		"Company": [
			{
				"fieldname": "hr_and_payroll_tab",
				"fieldtype": "Tab Break",
				"label": "HR & Payroll",
				"insert_after": "credit_limit",
			},
			{
				"fieldname": "hr_settings_section",
				"fieldtype": "Section Break",
				"label": "HR & Payroll Settings",
				"insert_after": "hr_and_payroll_tab",
			},
		],
	}

	create_custom_fields(custom_fields)
