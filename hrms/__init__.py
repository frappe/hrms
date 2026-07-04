import functools
import inspect

import frappe

__version__ = "16.12.0"


def refetch_resource(cache_key: str | list, user=None):
	frappe.publish_realtime(
		"hrms:refetch_resource",
		{"cache_key": cache_key},
		user=user or frappe.session.user,
		after_commit=True,
	)


def get_region(company=None):
	"""Return the country used to resolve regional overrides, based on flag,
	company or global settings. Mirrors erpnext.get_region.

	You can also set the global company flag in `frappe.flags.company`.
	"""
	if not company:
		company = frappe.local.flags.company

	if company:
		return frappe.get_cached_value("Company", company, "country")

	return frappe.flags.country or frappe.get_system_settings("country")


def allow_regional(fn):
	"""Decorator to make a function regionally overridable. Mirrors
	erpnext.allow_regional so HRMS functions can be overridden per region via the
	`regional_overrides` hook.

	Example:
	@hrms.allow_regional
	def myfunction():
	  pass"""

	@functools.wraps(fn)
	def caller(*args, **kwargs):
		overrides = frappe.get_hooks("regional_overrides", {}).get(get_region())
		function_path = f"{inspect.getmodule(fn).__name__}.{fn.__name__}"

		if not overrides or function_path not in overrides:
			return fn(*args, **kwargs)

		# Priority given to last installed app
		return frappe.get_attr(overrides[function_path][-1])(*args, **kwargs)

	return caller
