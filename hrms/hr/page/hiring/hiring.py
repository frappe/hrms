from collections import Counter, defaultdict

import frappe
from frappe import _
from frappe.utils import format_date, getdate

from hrms.hr.doctype.interview.interview import INTERVIEW_ACTIVE

STAGES = ["applied", "shortlisted", "interviewing", "offered", "hired", "rejected"]


def get_stage_labels() -> dict[str, str]:
	return {
		"applied": _("Applied"),
		"shortlisted": _("Shortlisted"),
		"interviewing": _("Interviewing"),
		"offered": _("Offered"),
		"hired": _("Hired"),
		"rejected": _("Rejected"),
	}


def get_interview_group_labels() -> dict[str, str]:
	return {
		"cleared": _("Cleared"),
		"feedback_in": _("Feedback in"),
		"not_cleared": _("Not cleared"),
		"feedback_due": _("Feedback due"),
		"no_panel": _("No interviewers"),
		"scheduled": _("Scheduled"),
	}


def get_rows(doctype, filters, fields, order_by=None, **kwargs):
	return frappe.get_list(doctype, filters=filters, fields=fields, order_by=order_by, limit=0, **kwargs)


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


def group_by(rows, key):
	grouped = defaultdict(list)
	for row in rows:
		grouped[row[key]].append(row)
	return grouped


def short_date(date):
	return format_date(date, "d MMM")


class ApplicantRecords:
	"""Offers, interviews and referrers of some applicants, loaded with one IN query per doctype."""

	def __init__(self, applicants):
		self.applicants = applicants
		names = [applicant.name for applicant in applicants]
		self.offers = defaultdict(list)
		self.interviews = defaultdict(list)
		self.panel_interviews = defaultdict(list)
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
			{"job_applicant": ["in", names], "docstatus": ["<", 2]},
			[
				"name",
				"job_applicant",
				"interview_type",
				"scheduled_on",
				"from_time",
				"to_time",
				"status",
				"docstatus",
				"creation",
				"modified",
			],
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
		# a cancelled draft stays out of the applicant's stage and attention, but the panel lists it
		# so it can be reopened
		self.panel_interviews = group_by(interviews, "job_applicant")
		self.interviews = group_by(
			[interview for interview in interviews if interview.status != "Cancelled"], "job_applicant"
		)

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

	def get_stage(self, applicant):
		"""The applicant's stored stage with the fact about it, and the hold and offer flags."""
		stage = applicant.stage.lower()
		offers = self.offers.get(applicant.name, [])
		interviews = self.interviews.get(applicant.name, [])
		latest = interviews[-1] if interviews else None
		# missing when the user can't read the applicant's interviews
		interview = latest if stage == "interviewing" else None
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
			"interview_group": get_interview_group(interview) if interview else None,
		}

	def get_fact(self, stage, applicant, offers, interview):
		if stage == "rejected":
			return applicant.rejection_reason or self.get_default_fact(applicant)
		if stage == "hired":
			return _("Offer accepted")
		if stage == "offered":
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


def is_not_cleared(interview) -> bool:
	"""The interview failed: it is marked rejected, or it has feedback and every feedback rejects."""
	results = getattr(interview, "feedback_results", None) or []
	return interview.status == "Rejected" or (
		interview.status in INTERVIEW_ACTIVE and bool(results) and all(r == "Rejected" for r in results)
	)


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


def get_applicant_stages(applicants) -> dict[str, dict]:
	"""Stage, fact, hold and offer flags per applicant name."""
	records = ApplicantRecords(applicants)
	return {applicant.name: records.get_stage(applicant) for applicant in applicants}


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
	stage: str = "applied",
	search: str | None = None,
	source: str | None = None,
	sort: str = "newest",
	start: int = 0,
	page_length: int = 50,
) -> dict:
	frappe.has_permission("Job Applicant", throw=True)
	frappe.has_permission("Job Opening", "read", doc=job_opening, throw=True)
	if stage not in STAGES:
		frappe.throw(_("Unknown stage {0}").format(stage))
	if sort not in PIPELINE_SORTS:
		frappe.throw(_("Unknown sort {0}").format(sort))

	counts = count_by("stage", {"job_title": job_opening})
	filters = {"job_title": job_opening, "stage": stage.title()}
	search_filters = get_search_filters(search)
	sources = count_by("source", filters, search_filters)
	if source:
		filters["source"] = source
	page = PipelinePage(stage, filters, search_filters, PIPELINE_SORTS[sort])
	page.load(int(start), int(page_length))

	return {
		"opening": get_opening_summary(job_opening),
		"counts": {name: counts[name.title()] for name in STAGES},
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

	def load(self, start, page_length):
		if self.stage == "interviewing":
			self.load_grouped(start, page_length)
			return
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

	def load_grouped(self, start, page_length):
		applicants = get_rows(
			"Job Applicant", self.filters, self.fields, self.order_by, or_filters=self.search_filters
		)
		self.stages = get_applicant_stages(applicants)
		groups = {a.name: get_row_group(self.stages[a.name]) for a in applicants}
		order = list(get_interview_group_labels())
		applicants.sort(key=lambda a: order.index(groups[a.name]))
		self.rows = applicants[start : start + page_length]
		self.total = len(applicants)
		self.groups = get_group_counts(groups)


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
	if info["stage"] != "interviewing":
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


def get_display_title(opening) -> str:
	"""The role name, with its location when another open role has the same name."""
	shares_name = frappe.db.exists(
		"Job Opening",
		{"job_title": opening.job_title, "status": "Open", "name": ["!=", opening.name]},
	)
	if shares_name and opening.location:
		return f"{opening.job_title} · {opening.location}"
	return opening.job_title


@frappe.whitelist(methods=["GET"])
def get_opening_header(job_opening: str) -> dict:
	frappe.has_permission("Job Opening", "read", doc=job_opening, throw=True)
	opening = get_opening_summary(job_opening)
	return {key: opening[key] for key in ("name", "display_title", "status", "designation")}


def get_applicant_onboarding(job_applicant):
	rows = get_rows("Employee Onboarding", {"job_applicant": job_applicant, "docstatus": ["<", 2]}, ["name"])
	return rows[0].name if rows else None


@frappe.whitelist(methods=["GET"])
def get_applicant_stage(job_applicant: str) -> dict:
	frappe.has_permission("Job Applicant", throw=True)
	frappe.has_permission("Job Applicant", "read", doc=job_applicant, throw=True)

	applicant = get_rows("Job Applicant", {"name": job_applicant}, APPLICANT_FIELDS)[0]
	info = get_applicant_stages([applicant])[applicant.name]
	return {
		"stage": info["stage"],
		"label": get_stage_labels()[info["stage"]],
		"fact": info["fact"],
		"job_opening": applicant.job_title,
		"onboarding": get_applicant_onboarding(applicant.name),
	}
