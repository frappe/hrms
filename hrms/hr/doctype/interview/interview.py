# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import datetime
from decimal import ROUND_HALF_UP, Decimal

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.functions import Avg
from frappe.utils import cint, cstr, flt, get_datetime, get_link_to_form, get_time, getdate, nowtime


class DuplicateInterviewRoundError(frappe.ValidationError):
	pass


class Interview(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.interview_detail.interview_detail import InterviewDetail

		amended_from: DF.Link | None
		applicant_name: DF.Data | None
		average_rating: DF.Rating
		designation: DF.Link | None
		expected_average_rating: DF.Rating
		from_time: DF.Time
		interview_details: DF.Table[InterviewDetail]
		interview_summary: DF.Text | None
		interview_type: DF.Link
		job_applicant: DF.Link
		job_opening: DF.Link | None
		reminded: DF.Check
		resume_link: DF.Data | None
		scheduled_on: DF.Date
		status: DF.Literal["Pending", "Under Review", "Cleared", "Rejected", "Cancelled"]
		to_time: DF.Time
	# end: auto-generated types

	def validate(self):
		validate_end_after_start(self.from_time, self.to_time)
		self.validate_interviewers()
		self.validate_duplicate_interview()
		self.validate_designation()

	def on_submit(self):
		if self.status not in ["Cleared", "Rejected"]:
			frappe.throw(
				_("Only Interviews with Cleared or Rejected status can be submitted."),
				title=_("Not Allowed"),
			)

	def before_update_after_submit(self):
		# a submitted interview has a result; it can switch between the two, never go back to undecided
		if self.status not in ["Cleared", "Rejected"]:
			frappe.throw(
				_("A submitted interview can only be Cleared or Rejected."),
				title=_("Not Allowed"),
			)

	def on_change(self):
		self.update_job_applicant_stage()

	def after_delete(self):
		self.update_job_applicant_stage()

	def update_job_applicant_stage(self):
		# imported here: job applicant imports this module
		from hrms.hr.doctype.job_applicant.job_applicant import update_stage

		update_stage(self.job_applicant)

	def validate_interviewers(self):
		if not any(d.interviewer for d in self.interview_details):
			frappe.throw(_("Add at least one interviewer"))

	def validate_duplicate_interview(self):
		if self.status == "Cancelled":
			return

		duplicate_interview = frappe.db.exists(
			"Interview",
			{
				"job_applicant": self.job_applicant,
				"interview_type": self.interview_type,
				"docstatus": ["<", 2],
				"status": ["!=", "Cancelled"],
				"name": ["!=", self.name],
			},
		)

		if duplicate_interview:
			frappe.throw(
				_(
					"Job Applicants are not allowed to appear twice for the same Interview Type. Interview {0} already scheduled for Job Applicant {1}"
				).format(
					frappe.bold(get_link_to_form("Interview", duplicate_interview)),
					frappe.bold(self.job_applicant),
				)
			)

	def validate_designation(self):
		applicant_designation = frappe.db.get_value("Job Applicant", self.job_applicant, "designation")
		if self.designation:
			if self.designation != applicant_designation:
				frappe.throw(
					_(
						"Interview Type {0} is only for Designation {1}. Job Applicant has applied for the role {2}"
					).format(self.interview_type, frappe.bold(self.designation), applicant_designation),
					exc=DuplicateInterviewRoundError,
				)
		else:
			self.designation = applicant_designation

	@frappe.whitelist(methods=["POST"])
	def reschedule_interview(
		self, scheduled_on: datetime.date, from_time: datetime.time, to_time: datetime.time
	) -> dict:
		"""Moves the interview. Returns {"rescheduled", "email_sent"}: the email is skipped
		(not an error) when no outgoing email account is set up."""
		validate_end_after_start(from_time, to_time)
		if (
			getdate(scheduled_on) == getdate(self.scheduled_on)
			and get_time(from_time) == get_time(self.from_time)
			and get_time(to_time) == get_time(self.to_time)
		):
			frappe.msgprint(
				_("Date and time haven't changed."), indicator="orange", title=_("Interview Not Rescheduled")
			)
			return {"rescheduled": False, "email_sent": False}

		original_date = self.scheduled_on
		original_from_time = self.from_time
		original_to_time = self.to_time

		self.db_set({"scheduled_on": scheduled_on, "from_time": from_time, "to_time": to_time})
		self.notify_update()

		email_sent = False
		if can_send_email():
			try:
				frappe.sendmail(
					recipients=get_recipients(self.name),
					subject=_("Interview: {0} Rescheduled").format(self.name),
					message=_(
						"Your Interview session is rescheduled from {0} {1} - {2} to {3} {4} - {5}"
					).format(
						original_date,
						original_from_time,
						original_to_time,
						self.scheduled_on,
						self.from_time,
						self.to_time,
					),
					reference_doctype=self.doctype,
					reference_name=self.name,
				)
				email_sent = True
			except frappe.OutgoingEmailError:
				pass

		return {"rescheduled": True, "email_sent": email_sent}

	def on_discard(self):
		self.db_set("status", "Cancelled")


INTERVIEW_ACTIVE = ("Pending", "Under Review")
INTERVIEW_RESULTS = ("Cleared", "Rejected")


def has_interviews(job_applicant: str) -> bool:
	"""The applicant has an interview that isn't cancelled."""
	return bool(
		frappe.db.exists(
			"Interview",
			{"job_applicant": job_applicant, "docstatus": ["<", 2], "status": ["!=", "Cancelled"]},
		)
	)


def has_cleared_interview(job_applicant: str) -> bool:
	"""One rule for "ready for an offer": an interview is cleared when its status says so,
	whether it is still a draft or already submitted."""
	return bool(
		frappe.db.exists(
			"Interview", {"job_applicant": job_applicant, "docstatus": ["<", 2], "status": "Cleared"}
		)
	)


def is_not_cleared(interview) -> bool:
	"""The interview failed: it is marked rejected, or it has feedback and every feedback rejects."""
	results = getattr(interview, "feedback_results", None) or []
	return interview.status == "Rejected" or (
		interview.status in INTERVIEW_ACTIVE and bool(results) and all(r == "Rejected" for r in results)
	)


@frappe.whitelist(methods=["POST"])
def submit_interview_results(job_applicant: str) -> dict:
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
		frappe.get_doc("Interview", draft.name).submit()
	return {
		"submitted": [draft.name for draft in drafts],
		"rejected": any(draft.status == "Rejected" for draft in drafts),
	}


def close_open_interviews(job_applicant: str, reviewed_status: str) -> list[dict]:
	"""Closes the applicant's drafts that still await a result: `reviewed_status` when someone already
	gave feedback, Cancelled otherwise. Not submitted. Returns the changed ones with their previous
	status, for an Undo."""
	drafts = frappe.get_all(
		"Interview",
		filters={"job_applicant": job_applicant, "docstatus": 0, "status": ["in", INTERVIEW_ACTIVE]},
		fields=["name", "status"],
	)
	has_feedback = get_interviews_with_feedback([draft.name for draft in drafts])
	for draft in drafts:
		save_interview_status(draft.name, reviewed_status if draft.name in has_feedback else "Cancelled")
	return [{"name": draft.name, "status": draft.status} for draft in drafts]


def restore_interviews(job_applicant: str, closed_interviews: list[dict]):
	"""The Undo of `close_open_interviews`: drafts of this applicant go back to their previous status."""
	for row in closed_interviews:
		current = frappe.db.get_value("Interview", row["name"], ["job_applicant", "docstatus"], as_dict=True)
		if not current or current.job_applicant != job_applicant or current.docstatus != 0:
			continue
		if row["status"] in INTERVIEW_ACTIVE:
			save_interview_status(row["name"], row["status"])


def reopen_closed_interviews(job_applicant: str):
	"""Drafts closed as Cancelled or Rejected wait for a result again: Pending when they are still
	ahead or nobody gave feedback, Under Review when feedback is in."""
	drafts = frappe.get_all(
		"Interview",
		filters={"job_applicant": job_applicant, "docstatus": 0, "status": ["in", ["Cancelled", "Rejected"]]},
		fields=["name", "scheduled_on"],
	)
	has_feedback = get_interviews_with_feedback([draft.name for draft in drafts])
	for draft in drafts:
		is_ahead = getdate(draft.scheduled_on) > getdate()
		is_reviewed = draft.name in has_feedback and not is_ahead
		save_interview_status(draft.name, "Under Review" if is_reviewed else "Pending")


def get_interviews_with_feedback(interviews: list[str]) -> set[str]:
	if not interviews:
		return set()
	return set(
		frappe.get_all(
			"Interview Feedback", filters={"interview": ["in", interviews], "docstatus": 1}, pluck="interview"
		)
	)


def save_interview_status(name: str, status: str):
	doc = frappe.get_doc("Interview", name)
	doc.status = status
	doc.flags.ignore_validate = True  # closing a draft must not depend on its panel being complete
	doc.flags.ignore_links = True  # link checks re-run fetch_from, which would overwrite e.g. designation
	doc.save()


def stars_from_rating(rating) -> float:
	"""A stored 0-1 rating as stars out of 5, rounded half up to 1 decimal (0.77 -> 3.9)."""
	stars = Decimal(str(flt(rating))) * 5
	return float(stars.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def can_send_email() -> bool:
	return bool(frappe.db.exists("Email Account", {"default_outgoing": 1, "enable_outgoing": 1}))


@frappe.whitelist()
def get_interviewers(interview_type: str) -> list[dict]:
	frappe.has_permission("Interview Type", "read", interview_type, throw=True)
	return frappe.get_all("Interviewer", filters={"parent": interview_type}, fields=["user as interviewer"])


def get_recipients(name, for_feedback=0):
	interview = frappe.get_doc("Interview", name)
	interviewers = [d.interviewer for d in interview.interview_details]

	if for_feedback:
		feedback_given_interviewers = frappe.get_all(
			"Interview Feedback", filters={"interview": name, "docstatus": 1}, pluck="interviewer"
		)
		recipients = [d for d in interviewers if d not in feedback_given_interviewers]
	else:
		recipients = interviewers
		recipients.append(frappe.db.get_value("Job Applicant", interview.job_applicant, "email_id"))

	return recipients


@frappe.whitelist()
def get_feedback(interview: str) -> list[dict]:
	frappe.has_permission("Interview", "read", interview, throw=True)
	frappe.has_permission("Interview Feedback", "read", throw=True)

	interview_feedback = frappe.qb.DocType("Interview Feedback")
	employee = frappe.qb.DocType("Employee")

	feedback = (
		frappe.qb.from_(interview_feedback)
		.select(
			interview_feedback.name,
			interview_feedback.modified.as_("added_on"),
			interview_feedback.interviewer.as_("user"),
			interview_feedback.feedback,
			interview_feedback.result,
			interview_feedback.average_rating.as_("total_score"),
			employee.employee_name.as_("reviewer_name"),
			employee.designation.as_("reviewer_designation"),
		)
		.left_join(employee)
		.on(interview_feedback.interviewer == employee.user_id)
		.where((interview_feedback.interview == interview) & (interview_feedback.docstatus == 1))
		.orderby(interview_feedback.creation)
	).run(as_dict=True)

	for row in feedback:
		row["total_score"] = stars_from_rating(row["total_score"])
	return feedback


@frappe.whitelist()
def get_skill_wise_average_rating(interview: str) -> list[dict]:
	frappe.has_permission("Interview", "read", interview, throw=True)
	skill_assessment = frappe.qb.DocType("Skill Assessment")
	interview_feedback = frappe.qb.DocType("Interview Feedback")
	return (
		frappe.qb.select(
			skill_assessment.skill,
			Avg(skill_assessment.rating).as_("rating"),
		)
		.from_(skill_assessment)
		.join(interview_feedback)
		.on(skill_assessment.parent == interview_feedback.name)
		.where((interview_feedback.interview == interview) & (interview_feedback.docstatus == 1))
		.groupby(skill_assessment.skill)
		.orderby(skill_assessment.idx)
	).run(as_dict=True)


@frappe.whitelist(methods=["POST"])
def update_job_applicant_status(status: str, job_applicant: str):
	try:
		if not job_applicant:
			frappe.throw(_("Please specify the job applicant to be updated."))

		doc = frappe.get_doc("Job Applicant", job_applicant)
		doc.status = status
		doc.save()

		frappe.msgprint(
			_("Updated the Job Applicant status to {0}").format(doc.status),
			alert=True,
			indicator="green",
		)
	except Exception:
		frappe.log_error("Failed to update Job Applicant status")
		frappe.msgprint(
			_("Failed to update the Job Applicant status"),
			alert=True,
			indicator="red",
		)


def send_interview_reminder():
	reminder_settings = frappe.db.get_value(
		"HR Settings",
		"HR Settings",
		["send_interview_reminder", "interview_reminder_template", "hiring_sender_email"],
		as_dict=True,
	)

	if not cint(reminder_settings.send_interview_reminder) or not can_send_email():
		return

	remind_before = cstr(frappe.db.get_single_value("HR Settings", "remind_before")) or "01:00:00"
	remind_before = datetime.datetime.strptime(remind_before, "%H:%M:%S")
	reminder_date_time = datetime.datetime.now() + datetime.timedelta(
		hours=remind_before.hour, minutes=remind_before.minute, seconds=remind_before.second
	)

	interviews = frappe.get_all(
		"Interview",
		filters=[
			["scheduled_on", "between", [datetime.datetime.now(), reminder_date_time]],
			["status", "=", "Pending"],
			["reminded", "=", 0],
			["docstatus", "!=", 2],
		],
	)

	interview_template = frappe.get_doc("Email Template", reminder_settings.interview_reminder_template)

	for d in interviews:
		doc = frappe.get_doc("Interview", d.name)
		context = doc.as_dict()
		message = frappe.render_template(interview_template.response, context)
		recipients = get_recipients(doc.name)

		frappe.sendmail(
			sender=reminder_settings.hiring_sender_email,
			recipients=recipients,
			subject=interview_template.subject,
			message=message,
			reference_doctype=doc.doctype,
			reference_name=doc.name,
		)

		doc.db_set("reminded", 1)


def send_daily_feedback_reminder():
	reminder_settings = frappe.db.get_value(
		"HR Settings",
		"HR Settings",
		[
			"send_interview_feedback_reminder",
			"feedback_reminder_notification_template",
			"hiring_sender_email",
		],
		as_dict=True,
	)

	if not cint(reminder_settings.send_interview_feedback_reminder) or not can_send_email():
		return

	interview_feedback_template = frappe.get_doc(
		"Email Template", reminder_settings.feedback_reminder_notification_template
	)

	interviews = frappe.get_all(
		"Interview",
		filters={
			"status": "Under Review",
			"docstatus": ["!=", 2],
			"scheduled_on": ["<=", getdate()],
			"to_time": ["<=", nowtime()],
		},
		pluck="name",
	)

	for interview in interviews:
		recipients = get_recipients(interview, for_feedback=1)

		doc = frappe.get_doc("Interview", interview)
		context = doc.as_dict()

		message = frappe.render_template(interview_feedback_template.response, context)

		if len(recipients):
			frappe.sendmail(
				sender=reminder_settings.hiring_sender_email,
				recipients=recipients,
				subject=interview_feedback_template.subject,
				message=message,
				reference_doctype="Interview",
				reference_name=interview,
			)


@frappe.whitelist()
def get_expected_skill_set(interview_type: str):
	frappe.has_permission("Interview Type", "read", interview_type, throw=True)
	return frappe.get_all(
		"Expected Skill Set", filters={"parent": interview_type}, fields=["skill"], order_by="idx"
	)


@frappe.whitelist(methods=["POST"])
def create_interview_feedback(data: str | dict, interview_name: str, interviewer: str, job_applicant: str):
	import json

	if isinstance(data, str):
		data = frappe._dict(json.loads(data))

	if frappe.session.user != interviewer:
		frappe.throw(_("Only the interview panel can submit feedback."))

	interview_feedback = frappe.new_doc("Interview Feedback")
	interview_feedback.interview = interview_name
	interview_feedback.interviewer = interviewer
	interview_feedback.job_applicant = job_applicant

	for d in data.skill_set:
		d = frappe._dict(d)
		interview_feedback.append("skill_assessment", d)

	interview_feedback.feedback = data.feedback
	interview_feedback.result = data.result

	interview_feedback.save()
	interview_feedback.submit()


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_interviewer_list(
	doctype: str, txt: str, searchfield: str, start: int, page_len: int, filters: dict
) -> list:
	filters = [
		["Has Role", "parent", "like", f"%{txt}%"],
		["Has Role", "role", "=", "interviewer"],
		["Has Role", "parenttype", "=", "User"],
	]

	if filters and isinstance(filters, list):
		filters.extend(filters)

	return frappe.get_all(
		"Has Role",
		limit_start=start,
		limit_page_length=page_len,
		filters=filters,
		fields=["parent"],
		as_list=1,
	)


@frappe.whitelist()
def get_events(start: str, end: str, filters: str | None = None):
	"""Returns events for Gantt / Calendar view rendering.

	:param start: Start date-time.
	:param end: End date-time.
	:param filters: Filters (JSON).
	"""
	from frappe.desk.calendar import get_event_conditions

	events = []

	event_color = {
		"Pending": "#fff4f0",
		"Under Review": "#d3e8fc",
		"Cleared": "#eaf5ed",
		"Rejected": "#fce7e7",
	}

	conditions = get_event_conditions("Interview", filters)

	# nosemgrep: frappe-semgrep-rules.rules.frappe-using-db-sql
	interviews = frappe.db.sql(
		f"""
			SELECT DISTINCT
				`tabInterview`.name, `tabInterview`.job_applicant, `tabInterview`.interview_type,
				`tabInterview`.scheduled_on, `tabInterview`.status, `tabInterview`.from_time as from_time,
				`tabInterview`.to_time as to_time
			from
				`tabInterview`
			where
				(`tabInterview`.scheduled_on between %(start)s and %(end)s)
				and docstatus != 2
				{conditions}
			""",
		{"start": start, "end": end},
		as_dict=True,
		update={"allDay": 0},
	)

	for d in interviews:
		subject_data = []
		for field in ["name", "job_applicant", "interview_type"]:
			if not d.get(field):
				continue
			subject_data.append(d.get(field))

		color = event_color.get(d.status)
		interview_data = {
			"from": get_datetime(
				"{scheduled_on} {from_time}".format(
					scheduled_on=d.scheduled_on, from_time=d.from_time or "00:00:00"
				)
			),
			"to": get_datetime(
				"{scheduled_on} {to_time}".format(
					scheduled_on=d.scheduled_on, to_time=d.to_time or "00:00:00"
				)
			),
			"name": d.name,
			"subject": "\n".join(subject_data),
			"color": color if color else "#89bcde",
		}

		events.append(interview_data)

	return events


def validate_end_after_start(from_time, to_time):
	if from_time and to_time and get_time(to_time) <= get_time(from_time):
		frappe.throw(_("End time must be after start time"))
