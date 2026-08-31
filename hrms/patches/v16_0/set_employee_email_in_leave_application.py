import frappe


def execute():
	leave_application = frappe.qb.DocType("Leave Application")
	employee = frappe.qb.DocType("Employee")

	rows = (
		frappe.qb.from_(leave_application)
		.join(employee)
		.on(leave_application.employee == employee.name)
		.select(leave_application.name, employee.user_id)
		.where(
			(employee.user_id.isnotnull())
			& (employee.user_id != "")
			& ((leave_application.employee_email.isnull()) | (leave_application.employee_email == ""))
		)
	).run(as_dict=True)

	if not rows:
		return

	updates = {row.name: {"employee_email": row.user_id} for row in rows}
	frappe.db.bulk_update("Leave Application", updates, update_modified=False)
