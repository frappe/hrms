from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import format_date, getdate

from hrms.hr.doctype.interview.interview import INTERVIEW_ACTIVE, is_not_cleared

APPLICANT_FIELDS = [
	"name",
	"applicant_name",
	"email_id",
	"status",
	"stage",
	"job_title",
	"source",
	"source_name",
	"employee_referral",
	"rejection_reason",
	"creation",
	"modified",
]


class ApplicantRecords:
	"""Offers, interviews and referrers of some applicants, loaded with one IN query per doctype."""

	def __init__(self, applicants):
		self.applicants = applicants
		names = [applicant.name for applicant in applicants]
		self.offers = defaultdict(list)
		self.interviews = defaultdict(list)
		self.referrers = {}
		if names:
			self.load(names)

	def load(self, names):
		self.offers = group_by(
			get_rows(
				"Job Offer",
				{"job_applicant": ["in", names], "docstatus": ["<", 2]},
				["name", "job_applicant", "status", "docstatus", "offer_date", "creation"],
				"creation asc",
			),
			"job_applicant",
		)
		self.load_interviews(names)
		self.load_referrers()

	def load_interviews(self, names):
		interviews = get_rows(
			"Interview",
			{"job_applicant": ["in", names], "docstatus": ["<", 2], "status": ["!=", "Cancelled"]},
			["name", "job_applicant", "interview_type", "scheduled_on", "status", "docstatus", "creation"],
			"scheduled_on asc, creation asc",
		)
		interview_names = [interview.name for interview in interviews]
		panels, feedback = {}, {}
		if interview_names:
			panel_rows = get_rows(
				"Interview Detail",
				{"parent": ["in", interview_names]},
				["parent", "interviewer"],
				parent_doctype="Interview",
			)
			feedback_rows = get_rows(
				"Interview Feedback",
				{"interview": ["in", interview_names], "docstatus": 1},
				["interview", "interviewer", "result"],
			)
			panels, feedback = group_by(panel_rows, "parent"), group_by(feedback_rows, "interview")
		for interview in interviews:
			interview.panel = [row.interviewer for row in panels.get(interview.name, [])]
			interview.feedback_from = [row.interviewer for row in feedback.get(interview.name, [])]
			interview.feedback_results = [row.result for row in feedback.get(interview.name, [])]
		self.interviews = group_by(interviews, "job_applicant")

	def load_referrers(self):
		referrals = {a.employee_referral for a in self.applicants if a.employee_referral}
		employees = {a.source_name for a in self.applicants if a.source_name}
		if referrals:
			for row in get_rows(
				"Employee Referral", {"name": ["in", list(referrals)]}, ["name", "referrer_name"]
			):
				self.referrers[row.name] = row.referrer_name
		if employees:
			for row in get_rows("Employee", {"name": ["in", list(employees)]}, ["name", "employee_name"]):
				self.referrers[row.name] = row.employee_name

	def get_referrer(self, applicant):
		return self.referrers.get(applicant.employee_referral) or self.referrers.get(applicant.source_name)

	def get_default_fact(self, applicant):
		referrer = self.get_referrer(applicant)
		if referrer:
			return _("Referred by {0}").format(referrer)
		return applicant.source or applicant.email_id or ""

	def get_stage_info(self, applicant):
		"""The applicant's stored stage with the fact about it, and the hold and offer flags."""
		stage = applicant.stage
		offers = self.offers.get(applicant.name, [])
		interviews = self.interviews.get(applicant.name, [])
		latest = interviews[-1] if interviews else None
		# missing when the user can't read the applicant's interviews
		interview = latest if stage == "Interviewing" else None
		can_make_offer = (
			bool(interview)
			and interview.status == "Cleared"
			and not any(offer.status != "Cancelled" for offer in offers)
		)
		return {
			"stage": stage,
			"fact": self.get_fact(stage, applicant, offers, interview),
			"on_hold": applicant.status == "Hold",
			"can_make_offer": can_make_offer,
			"interview": latest,
		}

	def get_fact(self, stage, applicant, offers, interview):
		if stage == "Rejected":
			return applicant.rejection_reason or self.get_default_fact(applicant)
		if stage == "Hired":
			return _("Offer accepted")
		if stage == "Offered":
			# as the applicant's own stage: any live offer that isn't answered counts, a draft too
			awaiting = [o for o in offers if o.status not in ("Rejected", "Cancelled", "Accepted")]
			if awaiting:
				return get_offer_fact(awaiting[-1])
		if interview:
			return get_interview_fact(interview)
		if applicant.status == "Accepted":
			return _("Ready for offer")
		return self.get_default_fact(applicant)


def get_offer_fact(offer):
	if offer.docstatus == 0 or offer.status == "Draft":
		return _("Offer in draft")
	if offer.status == "Ready to Send":
		return _("Offer ready to send")
	return _("Offer sent {0}").format(short_date(offer.offer_date or offer.creation))


def get_interview_fact(interview):
	parts = [interview.interview_type]
	if interview.status == "Cleared":
		parts.append(_("Cleared"))
	elif is_not_cleared(interview):
		parts.append(_("Not cleared"))
	else:
		parts.append(short_date(interview.scheduled_on))
		if is_feedback_due(interview):
			parts.append(_("Feedback {0} of {1}").format(len(interview.feedback_from), len(interview.panel)))
	return " · ".join(part for part in parts if part)


def is_feedback_due(interview):
	return (
		interview.panel
		and interview.status in INTERVIEW_ACTIVE
		and interview.scheduled_on
		and getdate(interview.scheduled_on) <= getdate()
	)


def get_rows(doctype, filters, fields, order_by=None, **kwargs):
	return frappe.get_list(doctype, filters=filters, fields=fields, order_by=order_by, limit=0, **kwargs)


def group_by(rows, key):
	grouped = defaultdict(list)
	for row in rows:
		grouped[row[key]].append(row)
	return grouped


def short_date(date):
	return format_date(date, "d MMM")
