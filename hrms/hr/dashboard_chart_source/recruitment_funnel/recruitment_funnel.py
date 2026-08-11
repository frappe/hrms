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

	JobApplicant = frappe.qb.DocType("Job Applicant")
	Interview = frappe.qb.DocType("Interview")
	JobOffer = frappe.qb.DocType("Job Offer")

	applicant_filters = {"docstatus": ["!=", 2]}
	applicant_subq = None

	if company:
		job_openings = frappe.get_all("Job Opening", filters={"company": company}, pluck="name")
		if not job_openings:
			return {
				"labels": [
					_("Applied"),
					_("Shortlisted"),
					_("Interviewed"),
					_("Offered"),
					_("Accepted"),
					_("Rejected"),
				],
				"datasets": [{"name": _("Applicants"), "values": [0, 0, 0, 0, 0, 0]}],
			}
		applicant_filters["job_title"] = ["in", job_openings]
		applicant_subq = (
			frappe.qb.from_(JobApplicant)
			.select(JobApplicant.name)
			.where(JobApplicant.docstatus != 2)
			.where(JobApplicant.job_title.isin(job_openings))
		)

	total = frappe.db.count("Job Applicant", applicant_filters)
	shortlisted = frappe.db.count("Job Applicant", {**applicant_filters, "status": "Shortlisted"})

	interview_query = (
		frappe.qb.from_(Interview).select(Interview.job_applicant).distinct().where(Interview.docstatus != 2)
	)
	if applicant_subq is not None:
		interview_query = interview_query.where(Interview.job_applicant.isin(applicant_subq))
	interviewed_names = (
		[row.job_applicant for row in interview_query.run(as_dict=True)] if total else []
	)

	offer_query = (
		frappe.qb.from_(JobOffer)
		.select(JobOffer.job_applicant, JobOffer.status)
		.where(JobOffer.docstatus == 1)
	)
	if applicant_subq is not None:
		offer_query = offer_query.where(JobOffer.job_applicant.isin(applicant_subq))
	all_offers = offer_query.run(as_dict=True) if total else []

	offer_names = {offer.job_applicant for offer in all_offers}
	interviewed = len(interviewed_names)
	offered = len(offer_names)
	accepted = len({offer.job_applicant for offer in all_offers if offer.status == "Accepted"})
	rejected = len({offer.job_applicant for offer in all_offers if offer.status == "Rejected"})

	return {
		"labels": [
			_("Applied"),
			_("Shortlisted"),
			_("Interviewed"),
			_("Offered"),
			_("Accepted"),
			_("Rejected"),
		],
		"datasets": [
			{
				"name": _("Applicants"),
				"values": [total, shortlisted, interviewed, offered, accepted, rejected],
			}
		],
	}
