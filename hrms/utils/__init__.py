from collections.abc import Generator

import requests

import frappe
from frappe.utils import add_days, date_diff

country_info = {}

# Cap the in-memory cache so a guest-reachable endpoint cannot grow it without bound
COUNTRY_INFO_CACHE_LIMIT = 10000


# pre-existing guest endpoint; this change only hardens the outbound request
@frappe.whitelist(allow_guest=True)  # nosemgrep: frappe-semgrep-rules.rules.security.guest-whitelisted-method
def get_country(fields: list | None = None) -> dict:
	global country_info
	ip = frappe.local.request_ip

	if ip not in country_info:
		lookup_fields = ["countryCode", "country", "regionName", "city"]
		try:
			res = requests.get(
				"https://pro.ip-api.com/json/{ip}?key={key}&fields={fields}".format(
					ip=ip, key=frappe.conf.get("ip-api-key"), fields=",".join(lookup_fields)
				),
				timeout=5,
			)
			info = res.json()
		except Exception:
			# network error, timeout or invalid JSON: return an empty result without
			# caching it, so a transient failure does not poison the cache for this IP
			return {}

		# avoid unbounded growth of the module-level cache
		if len(country_info) >= COUNTRY_INFO_CACHE_LIMIT:
			country_info.clear()
		country_info[ip] = info

	return country_info[ip]


def get_date_range(start_date: str, end_date: str) -> list[str]:
	"""returns list of dates between start and end dates"""
	no_of_days = date_diff(end_date, start_date) + 1
	return [add_days(start_date, i) for i in range(no_of_days)]


def generate_date_range(start_date: str, end_date: str, reverse: bool = False) -> Generator[str, None, None]:
	no_of_days = date_diff(end_date, start_date) + 1

	date_field = end_date if reverse else start_date
	direction = -1 if reverse else 1

	for n in range(no_of_days):
		yield add_days(date_field, direction * n)


def get_employee_email(employee_id: str) -> str | None:
	employee_emails = frappe.db.get_value(
		"Employee",
		employee_id,
		["prefered_email", "user_id", "company_email", "personal_email"],
		as_dict=True,
	)

	return (
		employee_emails.prefered_email
		or employee_emails.user_id
		or employee_emails.company_email
		or employee_emails.personal_email
	)


def extend_bootinfo(bootinfo):
	bootinfo.hr_only_setup = bool(frappe.conf.sk_hrms)
