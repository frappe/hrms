from frappe.custom.doctype.custom_field.custom_field import create_custom_field


def execute():
	create_custom_field(
		"Employee",
		{
			"fieldname": "default_appraisal_template",
			"fieldtype": "Link",
			"label": "Default Appraisal Template",
			"options": "Appraisal Template",
			"insert_after": "grade",
		},
	)
