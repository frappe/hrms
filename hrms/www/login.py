import frappe

from hrms.ameide_oidc import begin_login, normalize_redirect_to


def get_context(context):
	context.no_cache = 1
	redirect_to = normalize_redirect_to(
		frappe.form_dict.get("redirect-to") or frappe.form_dict.get("redirect_to")
	)
	begin_login(redirect_to)
