from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import add_to_date, now_datetime

from hrms.hr.doctype.interview.interview import (
	INTERVIEW_ACTIVE,
	close_open_interviews,
	has_interviews,
	reopen_closed_interviews,
	restore_interviews,
	stars_from_rating,
)
from hrms.hr.doctype.job_applicant.job_applicant import has_accepted_offer
from hrms.hr.page.hiring.hiring import (
	APPLICANT_FIELDS,
	ApplicantRecords,
	get_applicant_onboarding,
	get_rows,
	get_stage_labels,
	get_user_names,
	is_not_cleared,
)

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
INTERVIEW_RESULTS = ("Cleared", "Rejected")
OFFER_ANSWERS = ("Accepted", "Rejected")
OFFER_STATUSES = ("Ready to Send", "Awaiting Response", *OFFER_ANSWERS)
# where each submitted offer status may go; the reverse moves are the Undo of a change
OFFER_TRANSITIONS = {
	"Ready to Send": ("Awaiting Response", *OFFER_ANSWERS),
	"Awaiting Response": ("Ready to Send", *OFFER_ANSWERS),
	"Accepted": ("Ready to Send", "Awaiting Response"),
	"Rejected": ("Ready to Send", "Awaiting Response"),
}


@frappe.whitelist(methods=["GET"])
def get_applicant(job_applicant: str) -> dict:
	frappe.has_permission("Job Applicant", throw=True)
	frappe.has_permission("Job Applicant", "read", doc=job_applicant, throw=True)

	applicant = get_rows("Job Applicant", {"name": job_applicant}, APPLICANT_FIELDS + DETAIL_FIELDS)[0]
	records = ApplicantRecords([applicant])
	info = records.get_stage(applicant)
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
		"stage_label": get_stage_labels()[info["stage"]],
		"stage_since": get_stage_since(applicant, info, records),
		"fact": info["fact"],
		"on_hold": info["on_hold"],
		"can_make_offer": info["can_make_offer"],
		"interview_group": info["interview_group"],
		"current_interview": info["interview"].name if info["interview"] else None,
		"interviews": get_interviews(records, applicant.name),
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
	if info["stage"] == "applied":
		return applicant.creation
	if info["stage"] == "interviewing" and info["interview"]:
		return info["interview"].creation
	if info["stage"] in ("offered", "hired") and records.offers.get(applicant.name):
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


def get_interviews(records, applicant):
	interviews = list(reversed(records.panel_interviews.get(applicant, [])))
	feedback = get_feedback_by_interview([interview.name for interview in interviews])
	names = get_user_names({user for interview in interviews for user in interview.panel})
	result = []
	for interview in interviews:
		given = feedback.get(interview.name, {})
		ratings = [row.raw_rating for row in given.values() if row.raw_rating is not None]
		result.append(
			{
				"name": interview.name,
				"interview_type": interview.interview_type,
				"scheduled_on": interview.scheduled_on,
				"from_time": str(interview.from_time or ""),
				"to_time": str(interview.to_time or ""),
				"status": interview.status,
				"is_not_cleared": is_not_cleared(interview),
				"docstatus": interview.docstatus,
				"feedback_count": len(interview.feedback_from),
				"interviewer_count": len(interview.panel),
				"feedback_from": interview.feedback_from,
				"average_rating": stars_from_rating(sum(ratings) / len(ratings)) if ratings else None,
				"panel": [
					{
						"user": user,
						"full_name": names.get(user) or user,
						"result": given[user].result if user in given else None,
						"rating": given[user].rating if user in given else None,
					}
					for user in interview.panel
				],
			}
		)
	return result


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


def get_email_setup():
	sender = frappe.db.get_value(
		"Email Account",
		{"enable_outgoing": 1},
		"email_id",
		order_by="default_outgoing desc",
	)
	if sender:
		sender = frappe.db.get_single_value("HR Settings", "hiring_sender_email") or sender
	return {
		"can_send_email": bool(sender),
		"email_sender": sender,
		"can_set_up_email": bool(frappe.has_permission("Email Account", "create")),
	}


@frappe.whitelist(methods=["GET"])
def get_sender_account() -> dict:
	"""The outgoing account hiring mail goes from (the one the reject email uses), if any."""
	frappe.has_permission("Job Applicant", throw=True)
	return get_email_setup()


@frappe.whitelist(methods=["GET"])
def get_reject_details(job_applicant: str) -> dict:
	"""What the reject dialog needs about an applicant."""
	frappe.has_permission("Job Applicant", "read", doc=job_applicant, throw=True)
	name, applicant_name, email_id, opening = frappe.db.get_value(
		"Job Applicant", job_applicant, ["name", "applicant_name", "email_id", "job_title"]
	)
	return {
		"name": name,
		"applicant_name": applicant_name,
		"email_id": email_id,
		**get_opening_details(opening),
		**get_email_setup(),
	}


def set_status(job_applicant, status, reason=None, note=None):
	"""Saves the status. Leaving Rejected clears the reason and note (Job Applicant validate)."""
	doc = frappe.get_doc("Job Applicant", job_applicant)
	doc.status = status
	if status == "Rejected":
		doc.rejection_reason = reason or doc.rejection_reason
		doc.rejection_note = (note or "").strip() or doc.rejection_note
	doc.save()


@frappe.whitelist(methods=["POST"])
def reject_applicant(
	job_applicant: str,
	send_email: int = 0,
	subject: str | None = None,
	message: str | None = None,
	reason: str | None = None,
	note: str | None = None,
):
	"""Rejects an applicant with a reason and an optional note, optionally emailing them.
	The mail waits 30 seconds in the queue so Undo can cancel it."""
	frappe.has_permission("Job Applicant", "write", doc=job_applicant, throw=True)
	previous_status = frappe.db.get_value("Job Applicant", job_applicant, "status")
	set_status(job_applicant, "Rejected", reason, note)
	closed_interviews = close_open_interviews(job_applicant, "Rejected")

	communication = None
	if frappe.utils.cint(send_email):
		from frappe.core.doctype.communication.email import make

		result = make(
			doctype="Job Applicant",
			name=job_applicant,
			subject=subject,
			content=frappe.utils.escape_html(message or "").replace("\n", "<br>"),
			recipients=frappe.db.get_value("Job Applicant", job_applicant, "email_id"),
			sender=get_email_setup()["email_sender"],
			send_email=1,
			send_after=add_to_date(now_datetime(), seconds=30),
		)
		communication = result.get("name")
	return {
		"previous_status": previous_status,
		"communication": communication,
		"closed_interviews": closed_interviews,
	}


def has_cleared_interview(applicant) -> bool:
	"""One rule for "ready for an offer": an interview is cleared when its status says so,
	whether it is still a draft or already submitted."""
	return bool(
		frappe.db.exists(
			"Interview", {"job_applicant": applicant, "docstatus": ["<", 2], "status": "Cleared"}
		)
	)


@frappe.whitelist(methods=["GET"])
def get_offer_readiness(job_applicant: str) -> dict:
	"""Whether making an offer needs a confirmation: they were interviewed but none cleared."""
	frappe.has_permission("Job Applicant", "read", doc=job_applicant, throw=True)
	return {
		"has_cleared_interview": has_cleared_interview(job_applicant),
		"needs_confirmation": has_interviews(job_applicant) and not has_cleared_interview(job_applicant),
		"has_live_offer": bool(
			frappe.db.exists(
				"Job Offer",
				{
					"job_applicant": job_applicant,
					"docstatus": ["<", 2],
					"status": ["not in", ["Cancelled", "Rejected"]],
				},
			)
		),
		"has_accepted_offer": has_accepted_offer(job_applicant),
	}


@frappe.whitelist(methods=["POST"])
def move_back_applicant(job_applicant: str):
	"""Takes a rejected applicant back into the pipeline; the stage follows their interviews and offers."""
	frappe.has_permission("Job Applicant", "write", doc=job_applicant, throw=True)
	if frappe.db.get_value("Job Applicant", job_applicant, "status") != "Rejected":
		frappe.throw(_("Only a rejected applicant can be moved back."), frappe.ValidationError)
	reopen_closed_interviews(job_applicant)
	set_status(job_applicant, "Open")
	stage = frappe.db.get_value("Job Applicant", job_applicant, "stage").lower()
	return {"stage": stage, "stage_label": get_stage_labels()[stage]}


@frappe.whitelist(methods=["POST"])
def undo_reject_applicant(
	job_applicant: str,
	previous_status: str,
	communication: str | None = None,
	closed_interviews: str | list | None = None,
):
	"""Restores the status and the interviews the reject closed, and cancels the rejection email
	if it hasn't gone out yet."""
	frappe.has_permission("Job Applicant", "write", doc=job_applicant, throw=True)
	set_status(job_applicant, previous_status)
	restore_interviews(job_applicant, frappe.parse_json(closed_interviews) or [])
	return {"email_cancelled": cancel_queued_email(job_applicant, communication)}


def cancel_queued_email(job_applicant, communication) -> bool:
	"""Drops the applicant's email if it is still waiting in the queue."""
	if not communication:
		return False
	reference = frappe.db.get_value(
		"Communication", communication, ["reference_doctype", "reference_name"], as_dict=True
	)
	if not reference or (reference.reference_doctype, reference.reference_name) != (
		"Job Applicant",
		job_applicant,
	):
		return False

	queued = frappe.get_all(
		"Email Queue", filters={"communication": communication}, fields=["name", "status"]
	)
	if not queued or any(row.status != "Not Sent" for row in queued):
		return False
	# Email Queue can only be deleted by Administrator; the row belongs to this applicant, so drop it directly
	names = [row.name for row in queued]
	frappe.db.delete("Email Queue Recipient", {"parent": ["in", names]})
	frappe.db.delete("Email Queue", {"name": ["in", names]})
	frappe.delete_doc("Communication", communication, ignore_permissions=True, force=True)
	return True


@frappe.whitelist(methods=["POST"])
def set_interview_result(interview: str, status: str):
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


def submit_quietly(doc):
	"""Submits without the form's on_submit message; the page asks about rejecting in its own dialog."""
	logged = len(frappe.local.message_log)
	doc.submit()
	del frappe.local.message_log[logged:]


@frappe.whitelist(methods=["POST"])
def submit_interview(interview: str, status: str):
	"""Sets the result (Cleared or Rejected) and submits, in one step.
	`reject_applicant` tells the page to offer rejecting the applicant too."""
	frappe.has_permission("Interview", "submit", doc=interview, throw=True)
	doc = frappe.get_doc("Interview", interview)
	if doc.docstatus != 0:
		frappe.throw(_("This interview is already submitted or cancelled."), frappe.ValidationError)
	if status not in INTERVIEW_RESULTS:
		frappe.throw(_("An interview is submitted as cleared or rejected."), frappe.ValidationError)

	doc.status = status
	submit_quietly(doc)

	applicant = frappe.db.get_value(
		"Job Applicant", doc.job_applicant, ["name", "applicant_name", "status"], as_dict=True
	)
	should_offer_reject = doc.status == "Rejected" and applicant and applicant.status != "Rejected"
	return {
		"reject_applicant": bool(should_offer_reject),
		"applicant": applicant.name if applicant else None,
		"applicant_name": applicant.applicant_name if applicant else None,
	}


@frappe.whitelist(methods=["POST"])
def submit_interview_results(job_applicant: str):
	"""Submits the applicant's draft interviews that already have a result (Cleared or Rejected).

	Drafts still Pending or Under Review are left alone. Permission is checked for every interview
	before the first one is submitted, so a refusal names the interview and nothing is submitted."""
	frappe.has_permission("Job Applicant", "read", doc=job_applicant, throw=True)
	drafts = frappe.get_all(
		"Interview",
		filters={"job_applicant": job_applicant, "docstatus": 0, "status": ["in", INTERVIEW_RESULTS]},
		fields=["name", "interview_type", "status"],
		order_by="scheduled_on asc, creation asc",
	)
	for draft in drafts:
		if not frappe.has_permission("Interview", "submit", doc=draft.name):
			frappe.throw(
				_("You can't submit {0} ({1}).").format(draft.interview_type or draft.name, draft.name),
				frappe.PermissionError,
			)
	for draft in drafts:
		submit_quietly(frappe.get_doc("Interview", draft.name))
	return {
		"submitted": [draft.name for draft in drafts],
		"rejected": any(draft.status == "Rejected" for draft in drafts),
	}


@frappe.whitelist(methods=["POST"])
def set_offer_answer(
	job_offer: str,
	status: str,
	applicant_status: str | None = None,
	closed_interviews: str | list | None = None,
):
	"""Moves a submitted offer to Awaiting Response (sent), Accepted or Rejected (declined).

	Saving runs the offer's own hooks, which also set the applicant's status and close their open
	interviews. For an undo, pass the `previous_applicant_status` and `closed_interviews` the answer
	returned so the applicant and the interviews go back as well."""
	frappe.has_permission("Job Offer", "write", doc=job_offer, throw=True)
	doc = frappe.get_doc("Job Offer", job_offer)
	validate_offer_move(doc, status)

	previous_status = doc.status
	previous_applicant_status = (
		frappe.db.get_value("Job Applicant", doc.job_applicant, "status") if doc.job_applicant else None
	)
	doc.status = status
	doc.save()
	if applicant_status and doc.job_applicant and previous_applicant_status != applicant_status:
		set_status(doc.job_applicant, applicant_status)
	if doc.job_applicant:
		restore_interviews(doc.job_applicant, frappe.parse_json(closed_interviews) or [])
	return {
		"previous_status": previous_status,
		"previous_applicant_status": previous_applicant_status,
		"closed_interviews": doc.flags.closed_interviews or [],
	}


def validate_offer_move(offer, status):
	if status not in OFFER_STATUSES:
		frappe.throw(
			_("Offer status must be Ready to Send, Awaiting Response, Accepted or Rejected."),
			frappe.ValidationError,
		)
	if offer.docstatus != 1:
		frappe.throw(_("Only a submitted offer can be answered."), frappe.ValidationError)
	if status not in OFFER_TRANSITIONS.get(offer.status, ()):
		frappe.throw(
			_("The offer is {0}, so it can't be set to {1}.").format(offer.status, status),
			frappe.ValidationError,
		)
