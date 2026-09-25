import frappe


def execute():
	leave_application = frappe.qb.DocType("Leave Application")
	employee = frappe.qb.DocType("Employee")

	# Same fallback order as hrms.utils.get_employee_email(), fetched in one join instead of
	# a separate Employee lookup per row.
	rows = (
		frappe.qb.from_(leave_application)
		.join(employee)
		.on(leave_application.employee == employee.name)
		.select(
			leave_application.name,
			employee.prefered_email,
			employee.user_id,
			employee.company_email,
			employee.personal_email,
		)
		.where((leave_application.employee_email.isnull()) | (leave_application.employee_email == ""))
	).run(as_dict=True)

	if not rows:
		return

	updates = {}
	for row in rows:
		email = row.prefered_email or row.user_id or row.company_email or row.personal_email
		if email:
			updates[row.name] = {"employee_email": email}

	if updates:
		frappe.db.bulk_update("Leave Application", updates, update_modified=False)
