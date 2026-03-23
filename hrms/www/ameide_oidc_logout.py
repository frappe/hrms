import frappe


def get_context(context):
	context.no_cache = 1

	try:
		login_manager = getattr(frappe.local, "login_manager", None)
		if login_manager and hasattr(login_manager, "logout"):
			login_manager.logout()
	except Exception:
		pass

	frappe.local.flags.redirect_location = "/"
	raise frappe.Redirect

