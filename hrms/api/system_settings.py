import frappe


@frappe.whitelist(allow_guest=True, methods=["GET", "POST"], rate_limit=None)  # nosemgrep: guest-whitelisted-method  # fmt: skip
def get_user_pass_login_disabled():
	return frappe.get_system_settings("disable_user_pass_login")
