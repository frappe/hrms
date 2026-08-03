# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
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

	interview_detail = frappe.qb.DocType("Interview Detail")
	interview = frappe.qb.DocType("Interview")

	query = (
		frappe.qb.from_(interview_detail)
		.inner_join(interview)
		.on(interview_detail.parent == interview.name)
		.select(interview_detail.interviewer, interview.name.as_("interview_name"), interview.status)
		.where(interview.docstatus != 2)
		.where(interview_detail.parenttype == "Interview")
	)

	if company:
		job_openings = frappe.get_all("Job Opening", filters={"company": company}, pluck="name")
		company_applicants = frappe.get_all(
			"Job Applicant",
			filters={"docstatus": ["!=", 2]},
			or_filters=[
				["job_title", "in", job_openings or ["__no_match__"]],
				["job_title", "is", "not set"],
			],
			pluck="name",
		)
		if company_applicants:
			query = query.where(interview.job_applicant.isin(company_applicants))
		else:
			return {
				"labels": [],
				"datasets": [
					{"name": _("Total Interviews"), "values": []},
					{"name": _("Feedback Pending"), "values": []},
				],
			}

	rows = query.run(as_dict=True)

	feedback_submitted = {
		(f.interview, f.interviewer)
		for f in frappe.get_all(
			"Interview Feedback",
			filters={"docstatus": 1},
			fields=["interview", "interviewer"],
		)
	}

	interviewer_data = {}
	for row in rows:
		iv = row.interviewer
		if iv not in interviewer_data:
			interviewer_data[iv] = {"total": 0, "pending": 0}
		interviewer_data[iv]["total"] += 1
		if (row.interview_name, iv) not in feedback_submitted:
			interviewer_data[iv]["pending"] += 1

	sorted_ivs = sorted(
		interviewer_data.items(),
		key=lambda x: (x[1]["pending"], x[1]["total"]),
		reverse=True,
	)[:10]

	interviewer_emails = [iv[0] for iv in sorted_ivs]
	full_names = {
		u.name: u.full_name
		for u in frappe.get_all(
			"User", filters={"name": ["in", interviewer_emails]}, fields=["name", "full_name"]
		)
	}

	labels = [full_names.get(iv[0], iv[0]) for iv in sorted_ivs]
	totals = [iv[1]["total"] for iv in sorted_ivs]
	pending = [iv[1]["pending"] for iv in sorted_ivs]

	return {
		"labels": labels,
		"datasets": [
			{"name": _("Total Interviews"), "values": totals},
			{"name": _("Feedback Pending"), "values": pending},
		],
	}
