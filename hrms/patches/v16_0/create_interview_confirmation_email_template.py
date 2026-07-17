import frappe


def execute():
	if not frappe.db.exists("Email Template", "Interview Confirmation"):
		response = frappe.read_file(
			frappe.get_app_path("hrms", "hr", "doctype", "interview", "interview_confirmation_template.html")
		)

		frappe.get_doc(
			{
				"doctype": "Email Template",
				"name": "Interview Confirmation",
				"subject": "Interview Scheduled: {{ interview_type }} on {{ frappe.utils.formatdate(scheduled_on) }}",
				"response": response,
				"owner": frappe.session.user,
			}
		).insert(ignore_permissions=True)

	if not frappe.db.get_single_value("HR Settings", "interview_confirmation_template"):
		frappe.db.set_single_value("HR Settings", "send_interview_confirmation", 1)
		frappe.db.set_single_value("HR Settings", "interview_confirmation_template", "Interview Confirmation")
