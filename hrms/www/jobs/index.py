import frappe
from frappe import _
from frappe.query_builder import Order
from frappe.query_builder.functions import Count
from frappe.utils import pretty_date


def get_context(context):
	context.parents = [{"name": _("My Account"), "route": "/"}]
	context.body_class = "jobs-page"
	filters, txt, sort = get_filters_txt_and_sort()
	context.job_openings = get_job_openings(filters, txt, sort)
	context.all_filters = get_all_filters(filters)
	context.sort = sort


def get_job_openings(filters=None, txt=None, sort=None, limit_start=0, limit_page_length=20):

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
			jo.salary_per,
			jo.route,
			jo.location,
			jo.department,
			jo.employment_type,
			jo.company,
			jo.posted_on,
			jo.closes_on,
			Count(ja.job_title).as_("no_of_applications"),
		)
		.where((jo.status == "Open") & (jo.publish == 1))
		.groupby(jo.name)
	)

	for d in filters:
		query = query.where(frappe.qb.Field(d).isin(filters[d]))

	if txt:
		query = query.where((jo.job_title.like(f"%{txt}%")) | (jo.description.like(f"%{txt}%")))

	query = query.orderby("posted_on", order=Order.asc if sort == "asc" else Order.desc)

	results = query.run(as_dict=True)

	for d in results:
		d.posted_on = pretty_date(d.posted_on)

	return results


def get_all_filters(filters=None):
	job_openings = frappe.get_all(
		"Job Opening",
		filters={"publish": 1, "status": "Open"},
		fields=["company", "department", "location", "employment_type"],
	)

	companies = filters.get("company", [])

	all_filters = {}
	for opening in job_openings:
		for key, value in opening.items():
			if value and (key == "company" or not companies or opening.company in companies):
				all_filters.setdefault(key, set()).add(value)

	return {key: sorted(value) for key, value in all_filters.items()}


def get_filters_txt_and_sort():
	args = frappe.request.args.to_dict(flat=False)
	filters = {}
	txt = ""
	sort = None
	allowed_filters = ["company", "department", "location", "employment_type"]

	for d in args:
		if d in allowed_filters:
			filters[d] = args[d]
		elif d == "query":
			txt = args["query"][0]
		elif d == "sort":
			if args["sort"][0]:
				sort = args["sort"][0]

	return filters, txt, sort
