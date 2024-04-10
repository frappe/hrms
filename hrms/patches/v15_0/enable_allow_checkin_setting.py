import frappe


def execute():
	setting = frappe.get_doc("HR Settings")
	setting.allow_employee_checkin_from_mobile_app = 1
	setting.save()
