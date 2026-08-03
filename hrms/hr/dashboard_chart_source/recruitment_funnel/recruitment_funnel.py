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

	base_filters = {"docstatus": ["!=", 2]}

	if company:
		job_openings = frappe.get_all("Job Opening", filters={"company": company}, pluck="name")
		all_applicants = frappe.get_all(
			"Job Applicant",
			filters=base_filters,
			or_filters=[
				["job_title", "in", job_openings or ["__no_match__"]],
				["job_title", "is", "not set"],
			],
			fields=["name", "status"],
		)
	else:
		all_applicants = frappe.get_all(
			"Job Applicant",
			filters=base_filters,
			fields=["name", "status"],
		)

	applicant_names = [a.name for a in all_applicants]
	total = len(all_applicants)
	shortlisted = sum(1 for a in all_applicants if a.status == "Shortlisted")

	if applicant_names:
		interviewed = len(
			set(
				frappe.get_all(
					"Interview",
					filters={"docstatus": ["!=", 2], "job_applicant": ["in", applicant_names]},
					pluck="job_applicant",
				)
			)
		)
	else:
		interviewed = 0

	if company:
		all_offers = (
			frappe.get_all(
				"Job Offer",
				filters={"docstatus": 1, "job_applicant": ["in", applicant_names]},
				fields=["job_applicant", "status"],
			)
			if applicant_names
			else []
		)
	else:
		all_offers = frappe.get_all("Job Offer", filters={"docstatus": 1}, fields=["job_applicant", "status"])
	offered = len({o.job_applicant for o in all_offers})
	accepted = len({o.job_applicant for o in all_offers if o.status == "Accepted"})
	rejected = len({o.job_applicant for o in all_offers if o.status == "Rejected"})

	return {
		"labels": [_("Applied"), _("Shortlisted"), _("Interviewed"), _("Offered"), _("Accepted"), _("Rejected")],
		"datasets": [{"name": _("Applicants"), "values": [total, shortlisted, interviewed, offered, accepted, rejected]}],
	}
