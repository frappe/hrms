from frappe import get_site_config
from frappe.installer import update_site_config


def execute():
	old_user_type_limits = get_site_config().get("user_type_doctype_limit", None)
	if old_user_type_limits:
		new_user_type_limits = dict(old_user_type_limits)
		new_user_type_limits.pop("employee_self_service", None)
		update_site_config("user_type_doctype_limit", new_user_type_limits)
