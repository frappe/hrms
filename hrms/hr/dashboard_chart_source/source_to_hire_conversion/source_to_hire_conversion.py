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
	offer_filters = {"docstatus": 1, "status": "Accepted"}

	if company:
		job_openings = frappe.get_all("Job Opening", filters={"company": company}, pluck="name")
		applicants = frappe.get_all(
			"Job Applicant",
			filters=base_filters,
			or_filters=[
				["job_title", "in", job_openings or ["__no_match__"]],
				["job_title", "is", "not set"],
			],
			fields=["name", "source"],
		)
		offer_filters["company"] = company
	else:
		applicants = frappe.get_all(
			"Job Applicant",
			filters=base_filters,
			fields=["name", "source"],
		)

	accepted_applicants = set(
		frappe.get_all("Job Offer", filters=offer_filters, pluck="job_applicant")
	)

	source_data = {}
	for applicant in applicants:
		source = applicant.source or _("Unknown")
		if source not in source_data:
			source_data[source] = {"total": 0, "hired": 0}
		source_data[source]["total"] += 1
		if applicant.name in accepted_applicants:
			source_data[source]["hired"] += 1

	sorted_sources = sorted(source_data.items(), key=lambda x: x[1]["total"], reverse=True)[:8]

	labels = [s[0] for s in sorted_sources]
	totals = [s[1]["total"] for s in sorted_sources]
	hired = [s[1]["hired"] for s in sorted_sources]

	return {
		"labels": labels,
		"datasets": [
			{"name": _("Total Applicants"), "values": totals},
			{"name": _("Hired"), "values": hired},
		],
	}
