import frappe


def execute():
	activity = frappe.qb.DocType("Employee Boarding Activity")
	onboarding_rows = activity.parenttype == "Employee Onboarding"

	for status, flag in (("Completed", activity.completed), ("Skipped", activity.skipped)):
		frappe.qb.update(activity).set(flag, 1).where(onboarding_rows & (activity.status == status)).run()

	(
		frappe.qb.update(activity)
		.set(activity.status, None)
		.where(onboarding_rows & activity.status.notin(["In Progress", "Stuck"]))
	).run()
