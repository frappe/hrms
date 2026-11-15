from collections import Counter
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.utils import add_days, getdate, now_datetime

from hrms.hr.doctype.interview.interview import INTERVIEW_ACTIVE, is_not_cleared
from hrms.hr.doctype.job_applicant.stage_info import (
	APPLICANT_FIELDS,
	ApplicantRecords,
	get_rows,
	group_by,
	is_feedback_due,
	short_date,
)
from hrms.hr.doctype.job_opening.job_opening import get_display_title


def get_stages() -> list[str]:
	"""The stored stage values, in pipeline order."""
	return frappe.get_meta("Job Applicant").get_options("stage").split("\n")


def get_interview_group_labels() -> dict[str, str]:
	return {
		"cleared": _("Cleared"),
		"feedback_in": _("Feedback in"),
		"not_cleared": _("Not cleared"),
		"feedback_due": _("Feedback due"),
		"no_panel": _("No interviewers"),
		"scheduled": _("Scheduled"),
	}


def count_by(field, filters, or_filters=None) -> Counter:
	"""Job Applicants the user can read, counted per value of `field`."""
	rows = frappe.get_list(
		"Job Applicant",
		filters=filters,
		or_filters=or_filters,
		fields=[field, {"COUNT": "*", "as": "count"}],
		group_by=field,
	)
	return Counter({row[field]: row.count for row in rows})


def get_user_names(users):
	if not users:
		return {}
	rows = frappe.get_all("User", filters={"name": ["in", list(users)]}, fields=["name", "full_name"])
	return {row.name: row.full_name for row in rows}


def get_interview_group(interview) -> str:
	"""What happens next after the latest interview; first matching rule wins, HR's move first."""
	if interview.status == "Cleared":
		return "cleared"
	active = interview.status in INTERVIEW_ACTIVE
	if is_not_cleared(interview):
		return "not_cleared"
	if active and interview.panel and all(user in interview.feedback_from for user in interview.panel):
		return "feedback_in"
	if is_feedback_due(interview):
		return "feedback_due"
	if active and not interview.panel:
		return "no_panel"
	return "scheduled"


def get_interview_group_fact(interview) -> str:
	"""The row line under a group header: the header already says the state, so only round and date."""
	parts = [interview.interview_type, short_date(interview.scheduled_on)]
	if get_interview_group(interview) == "feedback_due" and len(interview.panel) > 1:
		parts.append(_("{0} of {1} in").format(len(interview.feedback_from), len(interview.panel)))
	return " · ".join(part for part in parts if part)


def get_page_stage_info(records, applicant) -> dict:
	"""The stage and its fact, with the hold and offer flags and the interview group the page acts by."""
	info = records.get_stage_info(applicant)
	interviews = records.interviews.get(applicant.name, [])
	latest = interviews[-1] if interviews else None
	# missing when the user can't read the applicant's interviews
	interview = latest if info["stage"] == "Interviewing" else None
	offers = records.offers.get(applicant.name, [])
	return {
		"stage": info["stage"],
		"fact": info["fact"],
		"on_hold": applicant.status == "Hold",
		"can_make_offer": bool(interview)
		and interview.status == "Cleared"
		and not any(offer.status != "Cancelled" for offer in offers),
		"interview": latest,
		"interview_group": get_interview_group(interview) if interview else None,
	}


def get_applicant_stages(applicants) -> dict[str, dict]:
	"""Page stage info per applicant name."""
	records = ApplicantRecords(applicants)
	return {applicant.name: get_page_stage_info(records, applicant) for applicant in applicants}


def get_department_names(departments):
	if not departments:
		return {}
	rows = get_rows("Department", {"name": ["in", list(departments)]}, ["name", "department_name"])
	return {row.name: row.department_name for row in rows}


# name breaks ties so pages don't overlap
PIPELINE_SORTS = {
	"newest": "creation desc, name desc",
	"oldest": "creation asc, name asc",
	"rating": "applicant_rating desc, creation desc, name desc",
}


@frappe.whitelist(methods=["GET"])
def get_pipeline(
	job_opening: str,
	stage: str = "Applied",
	search: str | None = None,
	source: str | None = None,
	sort: str = "newest",
	start: int = 0,
	page_length: int = 50,
	applicant: str | None = None,
) -> dict:
	"""One page of a stage's applicants; with `applicant`, the page grows to whole pages up to them."""
	frappe.has_permission("Job Applicant", throw=True)
	frappe.has_permission("Job Opening", "read", doc=job_opening, throw=True)
	if stage not in get_stages():
		frappe.throw(_("Unknown stage {0}").format(stage))
	if sort not in PIPELINE_SORTS:
		frappe.throw(_("Unknown sort {0}").format(sort))

	counts = count_by("stage", {"job_title": job_opening})
	filters = {"job_title": job_opening, "stage": stage}
	search_filters = get_search_filters(search)
	sources = count_by("source", filters, search_filters)
	if source:
		filters["source"] = source
	page = PipelinePage(stage, filters, search_filters, PIPELINE_SORTS[sort])
	page.load(int(start), int(page_length), applicant)

	return {
		"opening": get_opening_summary(job_opening),
		"counts": {name: counts[name] for name in get_stages()},
		"total": page.total,
		"sources": [
			{"source": name, "count": sources[name]} for name in sorted(name for name in sources if name)
		],
		"groups": page.groups,
		"rows": [get_pipeline_row(applicant, page.stages[applicant.name]) for applicant in page.rows],
	}


class PipelinePage:
	"""One page of a stage's applicants with their stage info, the stage total and its groups.
	Interviewing sorts by what happens next, which the records decide, so all its rows are loaded;
	the other stages page in the query."""

	def __init__(self, stage, filters, search_filters, order_by):
		self.stage = stage
		self.filters = filters
		self.search_filters = search_filters
		self.order_by = order_by
		self.fields = [*APPLICANT_FIELDS, "applicant_rating"]
		self.groups = []

	def load(self, start, page_length, applicant=None):
		if self.stage == "Interviewing":
			self.load_grouped(start, page_length, applicant)
			return
		if applicant:
			page_length = get_length_to(self.get_names()[start:], applicant, page_length)
		self.rows = frappe.get_list(
			"Job Applicant",
			filters=self.filters,
			or_filters=self.search_filters,
			fields=self.fields,
			order_by=self.order_by,
			offset=start,
			limit=page_length,
		)
		self.total = sum(count_by("stage", self.filters, self.search_filters).values())
		self.stages = get_applicant_stages(self.rows)

	def get_names(self):
		return frappe.get_list(
			"Job Applicant",
			filters=self.filters,
			or_filters=self.search_filters,
			order_by=self.order_by,
			pluck="name",
			limit=0,
		)

	def load_grouped(self, start, page_length, applicant=None):
		applicants = get_rows(
			"Job Applicant", self.filters, self.fields, self.order_by, or_filters=self.search_filters
		)
		self.stages = get_applicant_stages(applicants)
		groups = {a.name: get_row_group(self.stages[a.name]) for a in applicants}
		order = list(get_interview_group_labels())
		applicants.sort(key=lambda a: order.index(groups[a.name]))
		if applicant:
			page_length = get_length_to([a.name for a in applicants[start:]], applicant, page_length)
		self.rows = applicants[start : start + page_length]
		self.total = len(applicants)
		self.groups = get_group_counts(groups)


def get_length_to(names, applicant, page_length):
	"""Whole pages up to and including `applicant`; one page when they aren't listed."""
	if applicant not in names:
		return page_length
	return (names.index(applicant) // page_length + 1) * page_length


def get_pipeline_row(applicant, info):
	group = get_row_group(info)
	interview = info["interview"]
	return {
		"name": applicant.name,
		"applicant_name": applicant.applicant_name,
		"fact": info["fact"],
		"on_hold": info["on_hold"],
		"created": applicant.creation,
		"can_make_offer": info["can_make_offer"],
		"group": group,
		"group_fact": group and (get_interview_group_fact(interview) if interview else info["fact"]),
	}


def get_row_group(info):
	"""Interviewing rows are grouped; one whose interview the user can't read sits under Scheduled."""
	if info["stage"] != "Interviewing":
		return None
	return info["interview_group"] or "scheduled"


def get_group_counts(groups):
	counts = Counter(groups.values())
	return [
		{"group": group, "label": label, "count": counts[group]}
		for group, label in get_interview_group_labels().items()
		if counts[group]
	]


def get_search_filters(search):
	"""Name or email contains the search text, taken literally."""
	if not search:
		return None
	text = search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
	return {"applicant_name": ["like", f"%{text}%"], "email_id": ["like", f"%{text}%"]}


def get_opening_summary(job_opening):
	fields = ["name", "job_title", "status", "department", "location", "publish", "route"]
	fields += ["vacancies", "designation", "company"]
	opening = get_rows("Job Opening", {"name": job_opening}, fields)[0]
	if opening.department:
		opening.department = get_department_names({opening.department}).get(opening.department)
	opening.display_title = get_display_title(opening)
	return opening


def get_applicant_onboarding(job_applicant):
	rows = get_rows("Employee Onboarding", {"job_applicant": job_applicant, "docstatus": ["<", 2]}, ["name"])
	return rows[0].name if rows else None


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
		"stage": applicant.stage.lower(),
		"panel": [
			{"user": row.interviewer, "full_name": names.get(row.interviewer) or row.interviewer}
			for row in panels.get(interview.name, [])
		],
	}
