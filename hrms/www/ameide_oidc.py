from urllib.parse import quote

import frappe


def _normalize_redirect_to(value: str | None) -> str:
	if not value:
		return "/app"

	value = str(value).strip()
	if not value:
		return "/app"

	# Prevent open redirects.
	if "://" in value or value.startswith("//"):
		return "/app"

	if not value.startswith("/"):
		value = f"/{value}"

	return value


def get_context(context):
	context.no_cache = 1
	redirect_to = _normalize_redirect_to(frappe.form_dict.get("redirect-to") or frappe.form_dict.get("redirect_to"))
	frappe.form_dict["redirect_to"] = redirect_to

	try:
		from frappe.www.login import login_via_keycloak

		return login_via_keycloak()
	except Exception:
		frappe.local.flags.redirect_location = (
			"/api/method/frappe.www.login.login_via_keycloak?redirect_to=" + quote(redirect_to)
		)
		raise frappe.Redirect

