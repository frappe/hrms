import frappe


def execute():
	onboarding_template = frappe.qb.DocType("Employee Boarding Template")
	(
		frappe.qb.update(onboarding_template)
		.set(onboarding_template.title, onboarding_template.designation)
		.where(onboarding_template.title.isnull())
	).run()

	if not frappe.db.table_exists("Employee Separation Template"):
		return

	separation_template = frappe.qb.DocType("Employee Separation Template")
	(
		frappe.qb.update(separation_template)
		.set(separation_template.title, separation_template.designation)
		.where(separation_template.title.isnull())
	).run()
