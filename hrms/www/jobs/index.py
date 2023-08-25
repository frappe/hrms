import frappe
from frappe import _


def get_context(context):
	context.parents = [{"name": _("My Account"), "route": "/"}]
	context.job_openings = get_job_openings()


def get_job_openings(txt=None, filters=None, limit_start=0, limit_page_length=20, order_by=None):
	fields = [
		"name",
		"status",
		"job_title",
		"description",
		"publish_salary_range",
		"lower_range",
		"upper_range",
		"currency",
		"job_application_route",
		"salary_type",
		"route",
		"location",
		"department",
		"employment_type",
	]

	filters = filters or {}
	filters.update({"status": "Open"})

	if txt:
		filters.update(
			{"job_title": ["like", "%{0}%".format(txt)], "description": ["like", "%{0}%".format(txt)]}
		)

	return frappe.get_all(
		"Job Opening",
		filters,
		fields,
		start=limit_start,
		page_length=limit_page_length,
		order_by=order_by,
	)
