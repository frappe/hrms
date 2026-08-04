import os

import frappe
from frappe import _


def execute():
	response = frappe.read_file(
		os.path.join(
			frappe.get_app_path("hrms", "hr", "doctype"),
			"expense_claim/expense_claim_email_template.html",
		)
	)

	templates = [
		_("Expense Claim Approval Notification"),
		_("Expense Claim Status Notification"),
	]

	for template in templates:
		if frappe.db.exists("Email Template", template):
			continue

		frappe.get_doc(
			{
				"doctype": "Email Template",
				"name": template,
				"response": response,
				"subject": template,
				"owner": frappe.session.user,
			}
		).insert(ignore_permissions=True)

	hr_settings = frappe.get_doc("HR Settings")
	hr_settings.expense_claim_approval_notification_template = templates[0]
	hr_settings.expense_claim_status_notification_template = templates[1]
	hr_settings.save(ignore_permissions=True)
