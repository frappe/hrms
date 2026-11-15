import math
from collections import Counter

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
	published = get_published_openings()
	team_names = get_team_names([d.department for d in published])
	context.job_openings = get_job_openings(filters, txt, sort, page_len, offset, team_names=team_names)
	context.no_of_pages = get_no_of_pages(filters, txt, page_len)
	context.current_page = get_current_page(offset, page_len, context.no_of_pages)
	context.filter_controls = get_filter_controls(filters, published, team_names)
	context.hiring_company = get_hiring_company(published)
	context.has_openings = bool(published)
	context.has_filters = bool(filters or txt)
	context.query = txt
	context.sort = sort


def get_job_openings(filters=None, txt=None, sort=None, limit=20, offset=0, *, team_names):
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
		d.team = team_names.get(d.department, d.department)
	return results


def get_team_names(departments):
	departments = [d for d in set(departments) if d]
	if not departments:
		return {}
	return dict(
		frappe.get_all(
			"Department",
			filters={"name": ("in", departments)},
			fields=["name", "department_name"],
			as_list=True,
		)
	)


def get_current_page(offset, page_len, no_of_pages):
	return min(offset // page_len + 1, max(no_of_pages, 1))


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


FILTER_ORDER = ["location", "employment_type", "department", "company"]


def get_filter_label(name):
	return {
		"location": _("All locations"),
		"employment_type": _("All types"),
		"department": _("All teams"),
		"company": _("All companies"),
	}[name]


def get_field_label(name):
	return {
		"location": _("Location"),
		"employment_type": _("Type"),
		"department": _("Team"),
		"company": _("Company"),
	}[name]


def get_published_openings():
	return frappe.get_all(
		"Job Opening",
		filters={"publish": 1, "status": "Open"},
		fields=["company", "department", "employment_type", "location"],
	)


def get_all_filters(filters, openings):
	companies = filters.get("company", [])

	all_filters = {}
	for opening in openings:
		for key, value in opening.items():
			if value and (key == "company" or not companies or opening.company in companies):
				all_filters.setdefault(key, set()).add(value)

	return {key: sorted(value) for key, value in all_filters.items()}


def get_filter_controls(filters, openings, team_names):
	"""Selects for the toolbar; a select with nothing to choose stays hidden unless it is in use."""
	controls = []
	for key, values in get_all_filters(filters, openings).items():
		selected = filters.get(key, [])
		if len(values) < 2 and not selected:
			continue
		labels = get_option_labels(key, values, team_names)
		controls.append(
			{
				"name": key,
				"label": get_field_label(key),
				"all_label": get_filter_label(key),
				"options": [
					{"value": value, "label": labels[value], "selected": value in selected}
					for value in values
				],
			}
		)
	return sorted(controls, key=lambda control: FILTER_ORDER.index(control["name"]))


def get_option_labels(key, values, team_names):
	"""Teams show their short name, or the full Department name when two short names match."""
	if key != "department":
		return {value: value for value in values}
	labels = {value: team_names.get(value, value) for value in values}
	label_counts = Counter(labels.values())
	return {value: label if label_counts[label] == 1 else value for value, label in labels.items()}


def get_hiring_company(openings):
	"""The company the page intro names, when every opening is at the same one."""
	companies = {d.company for d in openings if d.company}
	return companies.pop() if len(companies) == 1 else ""


def get_filters_txt_sort_offset(page_len=20):
	args = frappe.request.args.to_dict(flat=False)
	filters = {}
	txt = ""
	sort = None
	offset = 0
	allowed_filters = ["company", "department", "employment_type", "location"]

	for d in args:
		if d in allowed_filters:
			values = [value for value in args[d] if value]
			if values:
				filters[d] = values
		elif d == "query":
			txt = args["query"][0]
		elif d == "sort":
			if args["sort"][0]:
				sort = args["sort"][0]
		elif d == "page":
			offset = (int(args["page"][0]) - 1) * page_len

	return filters, txt, sort, offset
