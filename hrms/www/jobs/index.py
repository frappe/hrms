import frappe
from frappe import _
from frappe.query_builder.functions import Count


def get_context(context):
	context.parents = [{"name": _("My Account"), "route": "/"}]
	args = frappe.request.args.to_dict(flat=False)
	filters, txt, context.order_by = get_filters_txt_and_order_by(args)
	context.job_openings = get_job_openings(filters, txt, context.order_by)
	context.all_filters = get_all_filters(filters)


def get_job_openings(filters=None, txt=None, order_by=None, limit_start=0, limit_page_length=20):

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

	for d in filters:
		query = query.where(frappe.qb.Field(d).isin(filters[d]))

	if txt:
		query = query.where((jo.job_title.like(f"%{txt}%")) | (jo.description.like(f"%{txt}%")))

	if order_by:
		print(order_by)

	return query.run(as_dict=True)


def get_all_filters(filters=None):
	job_openings = frappe.get_all(
		"Job Opening",
		fields=["company", "department", "location", "employment_type"],
	)

	companies = filters["company"] if "company" in filters else None

	all_filters = {}
	for d in job_openings:
		for key, value in d.items():
			if key == "company" or not companies or (companies and d["company"] in companies):
				if key not in all_filters:
					all_filters[key] = [value]
				elif value and value not in all_filters[key]:
					all_filters[key].append(value)

	for d in all_filters:
		all_filters[d].sort()

	return all_filters


def get_filters_txt_and_order_by(args):
	filters = {}
	txt = ""
	order_by = "Newest Post"
	allowed_filters = ["company", "department", "location", "employment_type"]
	for d in args:
		if d in allowed_filters:
			filters[d] = args[d]
		elif d == "query":
			txt = args["query"][0]
		elif d == "sort":
			if args["sort"][0] in ["Oldest Post", "Earliest Closing", "Latest Closing"]:
				order_by = args["sort"][0]
	return filters, txt, order_by
