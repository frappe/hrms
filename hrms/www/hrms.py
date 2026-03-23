import frappe
from frappe.boot import load_translations

from hrms.ameide_oidc import build_login_redirect_location, is_enabled

no_cache = 1


def get_context(context):
	if frappe.session.user == "Guest" and is_enabled():
		frappe.local.flags.redirect_location = build_login_redirect_location(_requested_hrms_path())
		raise frappe.Redirect

	csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()  # nosempgrep
	context = frappe._dict()
	context.csrf_token = csrf_token
	context.boot = get_boot()
	return context


@frappe.whitelist(methods=["POST"], allow_guest=True)
def get_context_for_dev():
	if not frappe.conf.developer_mode:
		frappe.throw(frappe._("This method is only meant for developer mode"))
	return get_boot()


def get_boot():
	bootinfo = frappe._dict(
		{
			"site_name": frappe.local.site,
			"push_relay_server_url": frappe.conf.get("push_relay_server_url") or "",
			"default_route": get_default_route(),
		}
	)

	bootinfo.lang = frappe.local.lang
	load_translations(bootinfo)

	return bootinfo


def get_default_route():
	return "/hrms"


def _requested_hrms_path():
	app_path = frappe.form_dict.get("app_path")
	if not app_path:
		return "/hrms"

	return f"/hrms/{str(app_path).lstrip('/')}"
