# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from frappe.query_builder.functions import Count
from frappe.utils.dashboard import cache_source


@frappe.whitelist()
@cache_source
def get_data(
	chart_name: str | None = None,
	chart: str | None = None,
	no_cache: str | None = None,
	filters: str | None = None,
	from_date: str | None = None,
	to_date: str | None = None,
	timespan: str | None = None,
	time_interval: str | None = None,
	heatmap_year: str | None = None,
) -> dict[str, list]:
	if filters:
		filters = frappe.parse_json(filters)
	else:
		filters = {}

	company = filters.get("company")

	JobApplicant = frappe.qb.DocType("Job Applicant")
	JobOffer = frappe.qb.DocType("Job Offer")

	query = (
		frappe.qb.from_(JobApplicant)
		.left_join(JobOffer)
		.on(
			(JobOffer.job_applicant == JobApplicant.name)
			& (JobOffer.docstatus == 1)
			& (JobOffer.status == "Accepted")
		)
		.select(JobApplicant.source, Count(JobApplicant.name).as_("total"), Count(JobOffer.job_applicant).distinct().as_("hired"))
		.where(JobApplicant.docstatus != 2)
		.groupby(JobApplicant.source)
	)

	if company:
		job_openings = frappe.get_all("Job Opening", filters={"company": company}, pluck="name")
		if not job_openings:
			return {
				"labels": [],
				"datasets": [
					{"name": _("Total Applicants"), "values": []},
					{"name": _("Hired"), "values": []},
				],
			}
		query = query.where(JobApplicant.job_title.isin(job_openings))

	rows = query.run(as_dict=True)
	rows.sort(key=lambda x: x.total, reverse=True)
	rows = rows[:8]

	return {
		"labels": [r.source or _("Unknown") for r in rows],
		"datasets": [
			{"name": _("Total Applicants"), "values": [r.total for r in rows]},
			{"name": _("Hired"), "values": [r.hired for r in rows]},
		],
	}
