import frappe

<<<<<<< HEAD
__version__ = "15.33.2"
=======
__version__ = "16.0.0-dev"
>>>>>>> da17577dc (chore: remove unused import)


def refetch_resource(cache_key: str | list, user=None):
	frappe.publish_realtime(
		"hrms:refetch_resource",
		{"cache_key": cache_key},
		user=user or frappe.session.user,
		after_commit=True,
	)
