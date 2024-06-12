import frappe
from frappe import _
from frappe.desk.doctype.notification_log.notification_log import make_notification_logs
from frappe.utils.user import get_system_managers


def execute():
	if "lending" in frappe.get_installed_apps():
		return

	if frappe.db.a_row_exists("Salary Slip Loan"):
		notify_existing_users()


def notify_existing_users():
	subject = _("WARNING: Loan Management module has been separated from ERPNext.") + "<br>"
	subject += _(
		"If you are using loans in salary slips, please install the {0} app from Frappe Cloud Marketplace or GitHub to continue using loan integration with payroll."
	).format(frappe.bold("Lending"))

	notification = {
		"subject": subject,
		"type": "Alert",
	}
	make_notification_logs(notification, get_system_managers(only_name=True))
