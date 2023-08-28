import frappe
from frappe import _
from frappe.query_builder.functions import Count


def get_context(context):
	context.parents = [{"name": _("My Account"), "route": "/"}]
	context.job_openings = get_job_openings()
	context.companies, context.departments, context.locations, context.employment_types = get_filters(
		context.job_openings
	)


def get_job_openings(txt=None, filters=None, limit_start=0, limit_page_length=20, order_by=None):
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

	return query.run(as_dict=True)

	# for filter in filters:
	# 	if filter == "from_date":
	# 		query = query.where(attendance.attendance_date >= filters.from_date)
	# 	elif filter == "to_date":
	# 		query = query.where(attendance.attendance_date <= filters.to_date)
	# 	elif filter == "consider_grace_period":
	# 		continue
	# 	elif filter == "late_entry" and not filters.consider_grace_period:
	# 		query = query.where(attendance.in_time > checkin.shift_start)
	# 	elif filter == "early_exit" and not filters.consider_grace_period:
	# 		query = query.where(attendance.out_time < checkin.shift_end)
	# 	else:
	# 		query = query.where(attendance[filter] == filters[filter])

	# if txt:
	# 	filters.update(
	# 		{"job_title": ["like", "%{0}%".format(txt)], "description": ["like", "%{0}%".format(txt)]}
	# 	)

	# return frappe.get_all(
	# 	"Job Opening",
	# 	filters,
	# 	fields,
	# 	start=limit_start,
	# 	page_length=limit_page_length,
	# 	order_by=order_by,
	# )


def get_filters(job_openings):
	companies, departments, locations, employment_types = ([] for _ in range(4))
	for d in job_openings:
		if d.company not in companies:
			companies.append(d.company)
		if d.department and d.department not in departments:
			departments.append(d.department)
		if d.location and d.location not in locations:
			locations.append(d.location)
		if d.employment_type and d.employment_type not in employment_types:
			employment_types.append(d.employment_type)
	companies.sort()
	departments.sort()
	locations.sort()
	employment_types.sort()
	return companies, departments, locations, employment_types
