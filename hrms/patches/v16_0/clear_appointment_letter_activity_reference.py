import frappe


def execute():
	activity = frappe.qb.DocType("Employee Boarding Activity")
	(
		frappe.qb.update(activity)
		.set(activity.reference_name, None)
		.where(
			(activity.parenttype == "Employee Preboarding")
			& (activity.action == "Appointment Letter")
			& activity.reference_name.isnotnull()
		)
	).run()
