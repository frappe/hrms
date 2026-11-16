from collections import Counter, defaultdict
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.utils import add_days, getdate, now_datetime, nowdate

from hrms.hr.doctype.interview.interview import INTERVIEW_ACTIVE
from hrms.hr.doctype.job_applicant.stage_info import APPLICANT_FIELDS, ApplicantRecords, get_rows, group_by
from hrms.hr.page.hiring.hiring import get_department_names, get_page_stage_info, get_user_names

OFFER_REPLY_DAYS = 7
ATTENTION_STAGES = {
	"no_reply": "Offered",
	"feedback": "Interviewing",
	"offer": "Interviewing",
	"decide": "Interviewing",
	"schedule": "Shortlisted",
	"review": "Applied",
	"onboard": "Hired",
}
OVERDUE_KINDS = ("no_reply", "feedback")
STUCK_KINDS = ("no_reply", "feedback", "offer", "decide")
OPENING_FIELDS = [
	"name",
	"job_title",
	"department",
	"location",
	"status",
	"closes_on",
	"closed_on",
	"vacancies",
	"creation",
]
# applicants with interviews or offers; a rejected one can still hold an offer that needs attention
RECORD_STAGES = ["Interviewing", "Offered", "Hired", "Rejected"]


@frappe.whitelist(methods=["GET"])
def get_overview() -> dict:
	"""Every opening with its applicant counts and what needs attention, for the Recruitment home."""
	frappe.has_permission("Job Applicant", throw=True)
	openings = get_rows("Job Opening", None, OPENING_FIELDS)
	counts = get_stage_counts()
	attention = get_attention_counts([row.name for row in openings if row.status == "Open"], counts)
	offers_out = get_offers_out()
	department_names = get_department_names({row.department for row in openings if row.department})
	for row in openings:
		stages = Counter()
		for (stage, _status), count in counts[row.name].items():
			stages[stage] += count
		row.update(
			department=department_names.get(row.department, row.department),
			applicants=sum(stages.values()),
			new=stages["Applied"],
			hired=stages["Hired"],
			offers_out=offers_out[row.name],
			active=stages["Interviewing"] + stages["Offered"],
			**get_attention(row, attention[row.name]),
		)
		row.needs_you = get_needs_you(row)
	return {"openings": sorted_openings(openings)}


def get_stage_counts() -> defaultdict:
	"""Counter of applicants per (stage, status), per opening."""
	rows = frappe.get_list(
		"Job Applicant",
		filters={"job_title": ["is", "set"]},
		fields=["job_title", "stage", "status", {"COUNT": "*", "as": "count"}],
		group_by="job_title, stage, status",
	)
	counts = defaultdict(Counter)
	for row in rows:
		counts[row.job_title][(row.stage, row.status)] += row.count
	return counts


def get_offers_out() -> Counter:
	"""Submitted offers still waiting for an answer, per job opening."""
	offers = get_rows(
		"Job Offer",
		{"docstatus": 1, "status": ["in", ["Ready to Send", "Awaiting Response"]]},
		["job_applicant"],
	)
	applicants = list({offer.job_applicant for offer in offers if offer.job_applicant})
	if not applicants:
		return Counter()
	openings = dict(
		get_rows(
			"Job Applicant",
			{"name": ["in", applicants], "job_title": ["is", "set"]},
			["name", "job_title"],
			as_list=True,
		)
	)
	return Counter(openings[offer.job_applicant] for offer in offers if offer.job_applicant in openings)


def get_stuck_label(kind, count) -> str:
	labels = {
		"no_reply": _("{0} offer awaiting reply") if count == 1 else _("{0} offers awaiting reply"),
		"feedback": _("{0} feedback due"),
		"offer": _("{0} ready for offer"),
		"decide": _("{0} to decide"),
	}
	return labels[kind].format(count)


def get_needs_you(opening):
	"""The one stuck item of an opening, or None. A filled opening with offers out comes first."""
	if opening.vacancies > 0 and opening.hired >= opening.vacancies and opening.offers_out > 0:
		label = _("{0} offer still out") if opening.offers_out == 1 else _("{0} offers still out")
		return {
			"label": label.format(opening.offers_out),
			"kind": "offers_out",
			"stage": "Offered",
			"is_late": True,
		}
	for entry in opening.attention:
		if entry["kind"] in STUCK_KINDS:
			return {
				"label": get_stuck_label(entry["kind"], entry["count"]),
				"kind": entry["kind"],
				"stage": ATTENTION_STAGES[entry["kind"]],
				"is_late": entry["kind"] in OVERDUE_KINDS,
			}
	return None


def get_attention(opening, counts):
	"""Attention entries of an open opening, most urgent first."""
	entries = [
		{"kind": kind, "count": counts[kind]}
		for kind in ATTENTION_STAGES
		if opening.status == "Open" and counts[kind]
	]
	return {
		"attention": entries,
		"attention_stage": ATTENTION_STAGES[entries[0]["kind"]] if entries else None,
		"is_overdue": any(entry["kind"] in OVERDUE_KINDS for entry in entries),
	}


def sorted_openings(openings):
	def last(value):
		return (value is None, value)

	def urgency(opening):
		total = sum(entry["count"] for entry in opening.attention)
		return (not opening.is_overdue, last(opening.closes_on), -total)

	open_ones = sorted((o for o in openings if o.status == "Open"), key=urgency)
	# a closed opening with candidates still interviewing or holding an offer is live work: it
	# follows the open ones, and the rest of the closed ones come last
	closed_ones = sorted(
		(o for o in openings if o.status != "Open"),
		key=lambda o: (not o.active, newest_first(o.closed_on)),
	)
	return open_ones + closed_ones


def newest_first(date):
	# an unset date sorts last, a later one first
	return (date is None, -getdate(date).toordinal() if date else 0)


def get_attention_counts(open_openings, counts) -> defaultdict:
	"""Counter of attention kinds per open opening, using the same rules the pipeline uses."""
	attention = defaultdict(Counter)
	for opening in open_openings:
		for (stage, status), count in counts[opening].items():
			if stage == "Applied":
				attention[opening]["review"] += count
			elif stage == "Shortlisted" and status != "Hold":
				attention[opening]["schedule"] += count
	if open_openings:
		count_record_attention(attention, open_openings)
	return attention


def count_record_attention(attention, open_openings):
	"""Adds the kinds that come from interviews and offers."""
	applicants = get_rows(
		"Job Applicant",
		{"job_title": ["in", open_openings], "stage": ["in", RECORD_STAGES]},
		APPLICANT_FIELDS,
	)
	live = [applicant for applicant in applicants if applicant.stage != "Rejected"]
	records = ApplicantRecords(live)
	for applicant in live:
		if get_page_stage_info(records, applicant)["can_make_offer"]:
			attention[applicant.job_title]["offer"] += 1
		for interview in records.interviews.get(applicant.name, []):
			kind = get_interview_kind(interview)
			if kind:
				attention[applicant.job_title][kind] += 1
	openings = {applicant.name: applicant.job_title for applicant in applicants}
	for applicant, kind in iter_offer_attention(list(openings)):
		attention[openings[applicant]][kind] += 1


def get_interview_kind(interview):
	if interview.docstatus != 0 or not interview.panel:
		return None
	if all(user in interview.feedback_from for user in interview.panel):
		return "decide"
	if interview.status in INTERVIEW_ACTIVE and getdate(interview.scheduled_on) < getdate():
		return "feedback"
	return None


def iter_offer_attention(applicants):
	"""Yield (applicant, kind) for offers of these applicants that wait too long or need onboarding."""
	if not applicants:
		return
	offers = get_rows(
		"Job Offer",
		{
			"docstatus": 1,
			"status": ["in", ["Awaiting Response", "Accepted"]],
			"job_applicant": ["in", applicants],
		},
		["name", "job_applicant", "status", "offer_date", "creation"],
	)
	handled = get_onboarded_offers(offers)
	for offer in offers:
		if offer.status == "Awaiting Response" and is_unanswered(offer):
			yield offer.job_applicant, "no_reply"
		elif offer.status == "Accepted" and offer.name not in handled:
			yield offer.job_applicant, "onboard"


def is_unanswered(offer):
	return bool(offer.offer_date) and getdate(offer.offer_date) <= getdate(
		add_days(nowdate(), -OFFER_REPLY_DAYS)
	)


def get_onboarded_offers(offers):
	"""Names of accepted offers that already have an onboarding or an employee."""
	accepted = [offer for offer in offers if offer.status == "Accepted"]
	if not accepted:
		return set()
	onboarding = get_rows(
		"Employee Onboarding",
		{"job_offer": ["in", [o.name for o in accepted]], "docstatus": ["<", 2]},
		["job_offer"],
	)
	employees = get_rows(
		"Employee", {"job_applicant": ["in", [o.job_applicant for o in accepted]]}, ["job_applicant"]
	)
	employed = {row.job_applicant for row in employees}
	handled = {row.job_offer for row in onboarding}
	return handled | {o.name for o in accepted if o.job_applicant in employed}


@frappe.whitelist(methods=["GET"])
def get_upcoming_interviews(days: int = 7, limit: int = 8) -> dict:
	"""Live interviews scheduled from today for `days` days, soonest first, for the Recruitment home."""
	frappe.has_permission("Job Applicant", throw=True)

	today = getdate()
	filters = {
		"docstatus": ["<", 2],
		"status": ["!=", "Cancelled"],
		"scheduled_on": ["between", [today, add_days(today, int(days) - 1)]],
	}
	rows = get_rows(
		"Interview",
		filters,
		["name", "interview_type", "scheduled_on", "from_time", "to_time", "job_applicant"],
		"scheduled_on asc, from_time asc, creation asc",
	)
	now = now_datetime()
	upcoming = [row for row in rows if get_interview_end(row) > now]
	return {"count": len(upcoming), "interviews": describe_upcoming(upcoming[: int(limit)])}


def get_interview_end(interview):
	"""When the interview ends; one without a time lasts until the end of its day."""
	end = interview.to_time or interview.from_time or timedelta(hours=23, minutes=59, seconds=59)
	return datetime.combine(getdate(interview.scheduled_on), (datetime.min + end).time())


def describe_upcoming(interviews):
	if not interviews:
		return []
	applicants = get_rows(
		"Job Applicant", {"name": ["in", [row.job_applicant for row in interviews]]}, APPLICANT_FIELDS
	)
	by_applicant = {applicant.name: applicant for applicant in applicants}
	opening_names = list({applicant.job_title for applicant in applicants if applicant.job_title})
	openings = dict(
		get_rows("Job Opening", {"name": ["in", opening_names]}, ["name", "job_title"], as_list=True)
	)
	panel_rows = get_rows(
		"Interview Detail",
		{"parent": ["in", [row.name for row in interviews]]},
		["parent", "interviewer"],
		parent_doctype="Interview",
	)
	panels = group_by(panel_rows, "parent")
	names = get_user_names({row.interviewer for row in panel_rows})
	return [
		get_upcoming_row(interview, by_applicant[interview.job_applicant], openings, panels, names)
		for interview in interviews
		if interview.job_applicant in by_applicant
	]


def get_upcoming_row(interview, applicant, openings, panels, names):
	return {
		"name": interview.name,
		"interview_type": interview.interview_type,
		"scheduled_on": interview.scheduled_on,
		"from_time": str(interview.from_time or ""),
		"job_applicant": applicant.name,
		"applicant_name": applicant.applicant_name,
		"job_opening": applicant.job_title,
		"opening_title": openings.get(applicant.job_title) or applicant.job_title,
		"stage": applicant.stage,
		"panel": [
			{"user": row.interviewer, "full_name": names.get(row.interviewer) or row.interviewer}
			for row in panels.get(interview.name, [])
		],
	}
