import frappe


def execute():
	onboarding_templates = frappe.db.get_list(
		"Employee Onboarding Template", fields=["name", "designation"]
	)

	for onboarding_template in onboarding_templates:
		frappe.db.set_value(
			"Employee Onboarding Template",
			onboarding_template.get("name"),
			{"title": onboarding_template.get("designation")},
		)
