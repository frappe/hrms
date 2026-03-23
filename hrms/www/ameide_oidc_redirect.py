import frappe

from hrms.ameide_oidc import complete_login


def get_context(context):
	context.no_cache = 1
	complete_login(
		frappe.form_dict.get("code"),
		frappe.form_dict.get("state"),
	)
