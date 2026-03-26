from frappe.custom.doctype.custom_field.custom_field import create_custom_field


def execute():
	create_custom_field(
		"Designation",
		{
			"fieldname": "appraisal_template",
			"fieldtype": "Link",
			"label": "Appraisal Template",
			"options": "Appraisal Template",
			"insert_after": "description",
			"allow_in_quick_entry": 1,
		},
	)
