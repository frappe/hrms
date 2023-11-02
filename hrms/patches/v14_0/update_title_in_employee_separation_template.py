import frappe


def execute():
	separation_templates = frappe.db.get_list(
		"Employee Separation Template", fields=["name", "designation"]
	)

	for separation_template in separation_templates:
		frappe.db.set_value(
			"Employee Separation Template",
			separation_template.get("name"),
			{"title": separation_template.get("designation")},
		)
