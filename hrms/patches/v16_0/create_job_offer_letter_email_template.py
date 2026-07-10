import frappe


def execute():
	if frappe.db.exists("Email Template", "Job Offer Letter"):
		return

	response = frappe.read_file(
		frappe.get_app_path("hrms", "hr", "doctype", "job_offer", "job_offer_email_template.html")
	)

	frappe.get_doc(
		{
			"doctype": "Email Template",
			"name": "Job Offer Letter",
			"response": response,
			"subject": "Job Offer: {{ designation }} at {{ company }}",
			"owner": frappe.session.user,
		}
	).insert(ignore_permissions=True)
