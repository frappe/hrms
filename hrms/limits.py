import requests

import frappe
from frappe import _


class PaywallReachedError(frappe.ValidationError):
	pass


def validate_employee_limit(doc, method):
	secret_key = frappe.conf.sk_hrms
	count = frappe.db.count("Employee")

	url = f"https://frappecloud.com/api/method/press.api.developer.saas.get_plan_config?secret_key={secret_key}"
	response = requests.request(method="POST", url=url, timeout=5)

	plan = response.json().get("message", {}).get("plan")
	if not plan:
		return

	limits = {"Basic": 25, "Essential": 50, "Professional": 100, "Enterprise": 0}

	if limits[plan] and count >= limits[plan]:
		frappe.throw(
			_("Only {} employees are allowed as per your plan.").format(limits[plan]),
			exc=PaywallReachedError,
		)
