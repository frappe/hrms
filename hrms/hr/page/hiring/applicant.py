from collections import defaultdict

import frappe
from frappe import _

from hrms.hr.doctype.interview.interview import (
	INTERVIEW_ACTIVE,
	INTERVIEW_RESULTS,
	is_not_cleared,
	stars_from_rating,
)
from hrms.hr.doctype.job_applicant.job_applicant import get_email_setup, set_applicant_status
from hrms.hr.doctype.job_applicant.stage_info import APPLICANT_FIELDS, ApplicantRecords, get_rows
from hrms.hr.page.hiring.hiring import get_applicant_onboarding, get_page_stage_info, get_user_names

DETAIL_FIELDS = [
	"phone_number",
	"designation",
	"cover_letter",
	"resume_attachment",
	"resume_link",
	"applicant_rating",
	"lower_range",
	"upper_range",
	"currency",
	"rejection_note",
]
RESPONSE_FIELDS = [
	"name",
	"applicant_name",
	"email_id",
	"status",
	"source",
	"rejection_reason",
	*DETAIL_FIELDS,
]


@frappe.whitelist(methods=["GET"])
def get_applicant(job_applicant: str) -> dict:
	frappe.has_permission("Job Applicant", throw=True)
	frappe.has_permission("Job Applicant", "read", doc=job_applicant, throw=True)

	applicant = get_rows("Job Applicant", {"name": job_applicant}, APPLICANT_FIELDS + DETAIL_FIELDS)[0]
	records = ApplicantRecords([applicant])
	info = get_page_stage_info(records, applicant)
	resume = get_resume_file(applicant.resume_attachment)
	return {
		**{field: applicant[field] for field in RESPONSE_FIELDS},
		"resume_attachment": applicant.resume_attachment if resume else None,
		"resume_file_name": resume.file_name if resume else None,
		"resume_uploaded_on": resume.creation if resume else None,
		"resume_missing": bool(applicant.resume_attachment) and not resume,
		"job_opening": applicant.job_title,
		**get_opening_details(applicant.job_title),
		"referred_by": records.get_referrer(applicant),
		"applied_on": applicant.creation,
		"stage": info["stage"],
		"stage_label": _(info["stage"]),
		"stage_since": get_stage_since(applicant, info, records),
		"fact": info["fact"],
		"on_hold": info["on_hold"],
		"can_make_offer": info["can_make_offer"],
		"interview_group": info["interview_group"],
		"current_interview": info["interview"].name if info["interview"] else None,
		"interviews": get_interviews(applicant.name),
		"offer": get_offer(records, applicant.name),
		"onboarding": get_applicant_onboarding(applicant.name),
		"emails": get_emails(applicant.name),
		"comments": get_comments(applicant.name),
		**get_email_setup(),
	}


@frappe.whitelist(methods=["POST"])
def mark_emails_seen(job_applicant: str):
	frappe.has_permission("Job Applicant", "read", doc=job_applicant, throw=True)
	frappe.db.set_value(
		"Communication",
		{
			"reference_doctype": "Job Applicant",
			"reference_name": job_applicant,
			"communication_type": "Communication",
			"sent_or_received": "Received",
			"seen": 0,
		},
		"seen",
		1,
		update_modified=False,
	)


def get_stage_since(applicant, info, records):
	if info["stage"] == "Applied":
		return applicant.creation
	if info["stage"] == "Interviewing" and info["interview"]:
		return info["interview"].creation
	if info["stage"] in ("Offered", "Hired") and records.offers.get(applicant.name):
		return records.offers[applicant.name][-1].creation

	version = frappe.get_all(
		"Version",
		filters={
			"ref_doctype": "Job Applicant",
			"docname": applicant.name,
			"data": ["like", '%"status"%'],
		},
		pluck="creation",
		order_by="creation desc",
		limit=1,
	)
	return version[0] if version else applicant.modified


def get_resume_file(file_url):
	if not file_url:
		return None
	return frappe.db.get_value("File", {"file_url": file_url}, ["file_name", "creation"], as_dict=True)


def get_interviews(applicant):
	"""The applicant's interviews, newest first; a cancelled draft is listed so it can be reopened."""
	interviews = get_rows(
		"Interview",
		{"job_applicant": applicant, "docstatus": ["<", 2]},
		["name", "interview_type", "scheduled_on", "from_time", "to_time", "status", "docstatus"],
		"scheduled_on desc, creation desc",
	)
	names = [interview.name for interview in interviews]
	panels = get_panels(names)
	feedback = get_feedback_by_interview(names)
	user_names = get_user_names({user for panel in panels.values() for user in panel})
	return [get_interview(interview, panels, feedback, user_names) for interview in interviews]


def get_interview(interview, panels, feedback, user_names):
	given = feedback.get(interview.name, {})
	ratings = [row.raw_rating for row in given.values() if row.raw_rating is not None]
	panel = panels.get(interview.name, [])
	interview.feedback_results = [row.result for row in given.values()]
	return {
		"name": interview.name,
		"interview_type": interview.interview_type,
		"scheduled_on": interview.scheduled_on,
		"from_time": str(interview.from_time or ""),
		"to_time": str(interview.to_time or ""),
		"status": interview.status,
		"is_not_cleared": is_not_cleared(interview),
		"docstatus": interview.docstatus,
		"feedback_count": len(given),
		"interviewer_count": len(panel),
		"feedback_from": list(given),
		"average_rating": stars_from_rating(sum(ratings) / len(ratings)) if ratings else None,
		"panel": [
			{
				"user": user,
				"full_name": user_names.get(user) or user,
				"result": given[user].result if user in given else None,
				"rating": given[user].rating if user in given else None,
			}
			for user in panel
		],
	}


def get_panels(interviews):
	"""Interviewers per interview."""
	panels = defaultdict(list)
	if interviews:
		rows = get_rows(
			"Interview Detail",
			{"parent": ["in", interviews]},
			["parent", "interviewer"],
			parent_doctype="Interview",
		)
		for row in rows:
			panels[row.parent].append(row.interviewer)
	return panels


def get_feedback_by_interview(interviews):
	"""Submitted feedback per interview and interviewer, with the rating on the 0 to 5 scale."""
	if not interviews:
		return {}
	rows = get_rows(
		"Interview Feedback",
		{"interview": ["in", interviews], "docstatus": 1},
		["interview", "interviewer", "result", "average_rating"],
	)
	feedback = defaultdict(dict)
	for row in rows:
		rating = None if row.average_rating is None else stars_from_rating(row.average_rating)
		feedback[row.interview][row.interviewer] = frappe._dict(
			result=row.result, rating=rating, raw_rating=row.average_rating
		)
	return feedback


def get_offer(records, applicant):
	offers = records.offers.get(applicant)
	if not offers:
		return None
	offer = offers[-1]
	return {field: offer[field] for field in ["name", "status", "docstatus", "offer_date", "creation"]}


def get_emails(applicant):
	return frappe.get_all(
		"Communication",
		filters={
			"reference_doctype": "Job Applicant",
			"reference_name": applicant,
			"communication_type": "Communication",
			"communication_medium": "Email",
		},
		fields=[
			"name",
			"subject",
			"content",
			"sender",
			"sender_full_name",
			"recipients",
			"cc",
			"communication_date",
			"sent_or_received",
			"seen",
			"delivery_status",
		],
		order_by="communication_date asc",
		limit=100,
	)


def get_comments(applicant):
	return frappe.get_all(
		"Comment",
		filters={
			"reference_doctype": "Job Applicant",
			"reference_name": applicant,
			"comment_type": "Comment",
		},
		fields=["name", "content", "comment_email", "comment_by", "creation"],
		order_by="creation asc",
	)


def get_opening_details(opening):
	details = frappe.db.get_value("Job Opening", opening, ["job_title", "company"], as_dict=True)
	return {"job_title": details.job_title, "company": details.company} if details else {}


@frappe.whitelist(methods=["POST"])
def shortlist_applicant(job_applicant: str) -> dict:
	"""Shortlists an applicant; `undo_shortlist_applicant` takes the returned status back."""
	frappe.has_permission("Job Applicant", "write", doc=job_applicant, throw=True)
	previous_status = frappe.db.get_value("Job Applicant", job_applicant, "status")
	set_applicant_status(job_applicant, "Shortlisted")
	return {"previous_status": previous_status}


@frappe.whitelist(methods=["POST"])
def undo_shortlist_applicant(job_applicant: str, previous_status: str):
	"""Restores the status from before the shortlist. A hold keeps the stage it is saved in, so an
	applicant held in Applied goes back to Applied first."""
	frappe.has_permission("Job Applicant", "write", doc=job_applicant, throw=True)
	if previous_status == "Hold":
		set_applicant_status(job_applicant, "Open")
	set_applicant_status(job_applicant, previous_status)


@frappe.whitelist(methods=["POST"])
def move_back_applicant(job_applicant: str) -> dict:
	"""Takes a rejected applicant back into the pipeline; the stage follows their interviews and offers."""
	frappe.has_permission("Job Applicant", "write", doc=job_applicant, throw=True)
	if frappe.db.get_value("Job Applicant", job_applicant, "status") != "Rejected":
		frappe.throw(_("Only a rejected applicant can be moved back."), frappe.ValidationError)
	set_applicant_status(job_applicant, "Open")
	stage = frappe.db.get_value("Job Applicant", job_applicant, "stage")
	return {"stage": stage, "stage_label": _(stage)}


@frappe.whitelist(methods=["POST"])
def set_interview_result(interview: str, status: str) -> dict:
	"""Sets the status of a draft interview and saves it; a draft's result (Cleared or Rejected) goes through
	`submit_interview`. A submitted interview can still switch between the two results."""
	if status not in (*INTERVIEW_RESULTS, *INTERVIEW_ACTIVE, "Cancelled"):
		frappe.throw(
			_("Interview status must be Pending, Under Review, Cleared, Rejected or Cancelled."),
			frappe.ValidationError,
		)
	frappe.has_permission("Interview", "write", doc=interview, throw=True)
	doc = frappe.get_doc("Interview", interview)
	is_switching_result = doc.docstatus == 1 and status in INTERVIEW_RESULTS
	if doc.docstatus != 0 and not is_switching_result:
		frappe.throw(
			_("A submitted interview can only switch between cleared and rejected."), frappe.ValidationError
		)
	previous_status = doc.status
	doc.status = status
	doc.save()
	return {"previous_status": previous_status}


@frappe.whitelist(methods=["POST"])
def submit_interview(interview: str, status: str) -> dict:
	"""Sets the result (Cleared or Rejected) and submits, in one step.
	`reject_applicant` tells the page to offer rejecting the applicant too."""
	frappe.has_permission("Interview", "submit", doc=interview, throw=True)
	doc = frappe.get_doc("Interview", interview)
	if doc.docstatus != 0:
		frappe.throw(_("This interview is already submitted or cancelled."), frappe.ValidationError)
	if status not in INTERVIEW_RESULTS:
		frappe.throw(_("An interview is submitted as cleared or rejected."), frappe.ValidationError)

	doc.status = status
	doc.submit()

	applicant = frappe.db.get_value(
		"Job Applicant", doc.job_applicant, ["name", "applicant_name", "status"], as_dict=True
	)
	should_offer_reject = doc.status == "Rejected" and applicant and applicant.status != "Rejected"
	return {
		"reject_applicant": bool(should_offer_reject),
		"applicant": applicant.name if applicant else None,
		"applicant_name": applicant.applicant_name if applicant else None,
	}
