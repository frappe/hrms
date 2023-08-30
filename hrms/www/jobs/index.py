import frappe
from frappe import _
from frappe.query_builder.functions import Count


def get_context(context):
	context.parents = [{"name": _("My Account"), "route": "/"}]
	applied_filters = frappe.request.args.to_dict(flat=False)
	context.job_openings = get_job_openings(applied_filters)
	context.filters = get_all_filters(applied_filters)


def get_job_openings(applied_filters=None, limit_start=0, limit_page_length=20, order_by=None):

	jo = frappe.qb.DocType("Job Opening")
	ja = frappe.qb.DocType("Job Applicant")

	query = (
		frappe.qb.from_(jo)
		.left_join(ja)
		.on(ja.job_title == jo.name)
		.select(
			jo.name,
			jo.status,
			jo.job_title,
			jo.description,
			jo.publish_salary_range,
			jo.lower_range,
			jo.upper_range,
			jo.currency,
			jo.job_application_route,
			jo.salary_type,
			jo.route,
			jo.location,
			jo.department,
			jo.employment_type,
			jo.company,
			jo.closes_on,
			Count(ja.job_title).as_("no_of_applications"),
		)
		.where(jo.status == "Open")
		.groupby(jo.name)
	)

	if "query" in applied_filters:
		search = f"%{applied_filters['query'][0]}%"
		query = query.where((jo.job_title.like(search)) | (jo.description.like(search)))
		del applied_filters["query"]

	for d in applied_filters:
		query = query.where(frappe.qb.Field(d).isin(applied_filters[d]))

	return query.run(as_dict=True)


def get_all_filters(applied_filters=None):
	job_openings = frappe.get_all(
		"Job Opening",
		fields=["company", "department", "location", "employment_type"],
	)

	companies = applied_filters["company"] if "company" in applied_filters else None

	filters = {}
	for d in job_openings:
		for key, value in d.items():
			if key == "company" or not companies or (companies and d["company"] in companies):
				if key not in filters:
					filters[key] = [value]
				elif value and value not in filters[key]:
					filters[key].append(value)

	for d in filters:
		filters[d].sort()

	return filters
