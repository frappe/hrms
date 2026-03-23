import frappe

from hrms.ameide_oidc import build_logout_redirect_location


def get_context(context):
	context.no_cache = 1
	id_token_hint = frappe.session.data.get("ameide_oidc_id_token")

	try:
		login_manager = getattr(frappe.local, "login_manager", None)
		if login_manager and hasattr(login_manager, "logout"):
			login_manager.logout()
	except Exception:
		pass

	frappe.local.flags.redirect_location = build_logout_redirect_location(id_token_hint)
	raise frappe.Redirect
