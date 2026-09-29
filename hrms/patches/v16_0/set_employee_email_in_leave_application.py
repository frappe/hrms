import frappe

BATCH_SIZE = 1000


def execute():
	# A row with no resolvable email at all never leaves the WHERE clause's match set, so
	# batching can't rely on updates shrinking it — walk forward by name instead, which
	# guarantees progress regardless of how many rows turn out to be unresolvable.
	last_name = ""
	while rows := get_next_batch(last_name):
		updates = {}
		for row in rows:
			email = row.prefered_email or row.user_id or row.company_email or row.personal_email
			if email:
				updates[row.name] = {"employee_email": email}

		if updates:
			frappe.db.bulk_update("Leave Application", updates, update_modified=False)

		last_name = rows[-1].name


def get_next_batch(after_name):
	leave_application = frappe.qb.DocType("Leave Application")
	employee = frappe.qb.DocType("Employee")

	# Same fallback order as hrms.utils.get_employee_email(), fetched in one join instead of
	# a separate Employee lookup per row.
	query = (
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
		.orderby(leave_application.name)
		.limit(BATCH_SIZE)
	)
	if after_name:
		query = query.where(leave_application.name > after_name)
	return query.run(as_dict=True)
