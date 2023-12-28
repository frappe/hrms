import frappe

__version__ = "16.0.0-dev"


def refetch_resource(cache_key: str | list, user=None):
	frappe.publish_realtime(
		"hrms:refetch_resource",
		{"cache_key": cache_key},
		user=user or frappe.session.user,
		after_commit=True,
	)
