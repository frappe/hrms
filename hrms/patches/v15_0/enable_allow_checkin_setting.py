import frappe


def execute():
	settings = frappe.get_single("HR Settings")
	settings.allow_employee_checkin_from_mobile_app = 1
	settings.flags.ignore_mandatory = True
	settings.flags.ignore_permissions = True
	settings.save()
