import frappe


def execute():
	if not frappe.db.has_column("Employee Boarding Activity", "depends_on_activity"):
		return

	activity = frappe.qb.DocType("Employee Boarding Activity")
	(
		frappe.qb.update(activity)
		.set(activity.depends_on_action, activity.depends_on_activity)
		.where(activity.depends_on_activity.isnotnull() & (activity.depends_on_action.isnull()))
	).run()
