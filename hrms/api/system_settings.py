import frappe


@frappe.whitelist(allow_guest=True)
def get_user_pass_login_disabled():
	return frappe.get_system_settings("disable_user_pass_login")
