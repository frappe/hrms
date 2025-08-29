import math

import frappe
from frappe import _
from frappe.query_builder import Order
from frappe.query_builder.functions import Count
from frappe.utils import pretty_date


def get_context(context):
	context.no_cache = 1
	if frappe.session.user == "Guest":
		context.parents = [{"name": _("Home"), "route": "/"}]
	else:
		context.parents = [{"name": _("My Account"), "route": "/me"}]
	context.body_class = "jobs-page"
	page_len = 20
	filters, txt, sort, offset = get_filters_txt_sort_offset(page_len)
	context.job_openings = get_job_openings(filters, txt, sort, page_len, offset)
	context.no_of_pages = get_no_of_pages(filters, txt, page_len)
	context.all_filters = get_all_filters(filters)
	context.sort = sort


def get_job_openings(filters=None, txt=None, sort=None, limit=20, offset=0):
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
			jo.publish_applications_received,
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
		.limit(limit)
		.offset(offset)
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


def get_no_of_pages(filters=None, txt=None, page_length=20):
	jo = frappe.qb.DocType("Job Opening")
	query = (
		frappe.qb.from_(jo)
		.select(
			Count("*").as_("no_of_openings"),
		)
		.where((jo.status == "Open") & (jo.publish == 1))
	)

	for d in filters:
		query = query.where(frappe.qb.Field(d).isin(filters[d]))

	if txt:
		query = query.where((jo.job_title.like(f"%{txt}%")) | (jo.description.like(f"%{txt}%")))

	result = query.run(as_dict=True)
	return math.ceil(result[0].no_of_openings / page_length)


def get_all_filters(filters=None):
	job_openings = frappe.get_all(
		"Job Opening",
		filters={"publish": 1, "status": "Open"},
		fields=["company", "department", "employment_type", "location"],
	)

	companies = filters.get("company", [])

	all_filters = {}
	for opening in job_openings:
		for key, value in opening.items():
			if value and (key == "company" or not companies or opening.company in companies):
				all_filters.setdefault(key, set()).add(value)

	return {key: sorted(value) for key, value in all_filters.items()}


def get_filters_txt_sort_offset(page_len=20):
	args = frappe.request.args.to_dict(flat=False)
	filters = {}
	txt = ""
	sort = None
	offset = 0
	allowed_filters = ["company", "department", "employment_type", "location"]

	for d in args:
		if d in allowed_filters:
			filters[d] = args[d]
		elif d == "query":
			txt = args["query"][0]
		elif d == "sort":
			if args["sort"][0]:
				sort = args["sort"][0]
		elif d == "page":
			offset = (int(args["page"][0]) - 1) * page_len

	return filters, txt, sort, offset
