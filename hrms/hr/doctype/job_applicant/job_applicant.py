# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

# For license information, please see license.txt


import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import append_number_if_name_exists
from frappe.utils import flt, now_datetime, time_diff_in_seconds, validate_email_address

from hrms.hr.doctype.interview.interview import get_interviewers


class DuplicationError(frappe.ValidationError):
	pass


class JobApplicant(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.job_applicant_status_change_log.job_applicant_status_change_log import (
			JobApplicantStatusChangeLog,
		)

		applicant_name: DF.Data
		applicant_rating: DF.Rating
		country: DF.Link | None
		cover_letter: DF.Text | None
		currency: DF.Link | None
		designation: DF.Link | None
		email_id: DF.Data
		employee_referral: DF.Link | None
		job_title: DF.Link | None
		lower_range: DF.Currency
		notes: DF.Data | None
		phone_number: DF.Data | None
		resume_attachment: DF.Attach | None
		resume_link: DF.Data | None
		source: DF.Link | None
		source_name: DF.Link | None
		status: DF.Link
		status_change_log: DF.Table[JobApplicantStatusChangeLog]
		status_entered_on: DF.Datetime | None
		upper_range: DF.Currency
	# end: auto-generated types

	def onload(self):
		job_offer = frappe.get_all("Job Offer", filters={"job_applicant": self.name})
		if job_offer:
			self.get("__onload").job_offer = job_offer[0].name

	def autoname(self):
		self.name = self.email_id

		# applicant can apply more than once for a different job title or reapply
		if frappe.db.exists("Job Applicant", self.name):
			self.name = append_number_if_name_exists("Job Applicant", self.name)

	def validate(self):
		if self.email_id:
			validate_email_address(self.email_id, True)

		if self.employee_referral:
			self.set_status_for_employee_referral()

		if not self.applicant_name and self.email_id:
			guess = self.email_id.split("@")[0]
			self.applicant_name = " ".join([p.capitalize() for p in guess.split(".")])

	def before_insert(self):
		if self.job_title:
			job_opening_status = frappe.db.get_value("Job Opening", self.job_title, "status")
			if job_opening_status == "Closed":
				frappe.throw(
					_("Cannot create a Job Applicant against a closed Job Opening"), title=_("Not Allowed")
				)

	def before_save(self):
		self.track_status_change()

	def set_status_for_employee_referral(self):
		emp_ref = frappe.get_doc("Employee Referral", self.employee_referral)
		if self.status in ["Open", "Replied", "Hold"]:
			emp_ref.db_set("status", "In Process")
		elif self.status in ["Accepted", "Rejected"]:
			emp_ref.db_set("status", self.status)

	def track_status_change(self):
		"""
		Maintains `status_entered_on` and appends an entry to
		`status_change_log` whenever the applicant's status changes.
		"""
		if self.is_new():
			self.status_entered_on = now_datetime()
			return

		doc_before_save = self.get_doc_before_save()
		previous_status = doc_before_save.status if doc_before_save else None

		if previous_status and previous_status != self.status:
			time_in_previous_status = 0
			if self.status_entered_on:
				time_in_previous_status = time_diff_in_seconds(now_datetime(), self.status_entered_on)

			self.append(
				"status_change_log",
				{
					"previous_status": previous_status,
					"new_status": self.status,
					"changed_by": frappe.session.user,
					"changed_on": now_datetime(),
					"time_in_previous_status": time_in_previous_status,
				},
			)
			self.status_entered_on = now_datetime()


COLOR_TO_INDICATOR = {
	"#bd3e0c": "Orange",
	"#0070cc": "Blue",
	"#b52a2a": "Red",
	"#16794c": "Green",
}

KANBAN_COLUMNS = ["Open", "Replied", "Shortlisted", "Accepted"]


@frappe.whitelist()
def create_kanban_board(board_name: str) -> dict:
	frappe.has_permission("Job Applicant", throw=True)

	if frappe.db.exists("Kanban Board", board_name):
		return frappe.get_doc("Kanban Board", board_name).as_dict()

	statuses = frappe.get_all(
		"Job Applicant Status",
		fields=["status_name", "color"],
		filters={"status_name": ["in", KANBAN_COLUMNS]},
		order_by="sequence asc",
	)

	board = frappe.new_doc("Kanban Board")
	board.kanban_board_name = board_name
	board.reference_doctype = "Job Applicant"
	board.field_name = "status"
	board.private = 0
	board.fields = json.dumps(["designation", "applicant_rating"])
	board.show_labels = 1

	for d in statuses:
		board.append(
			"columns",
			{
				"column_name": d.status_name,
				"status": "Active",
				"indicator": COLOR_TO_INDICATOR.get(d.color, "Gray"),
			},
		)

	board.insert(ignore_permissions=True)
	return board.as_dict()


@frappe.whitelist()
def create_interview(job_applicant: str, interview_type: str) -> Document:
	doc = frappe.get_doc("Job Applicant", job_applicant)

	round_designation = frappe.db.get_value("Interview Type", interview_type, "designation")

	if round_designation and doc.designation and round_designation != doc.designation:
		frappe.throw(
			_("Interview Type {0} is only applicable for the Designation {1}").format(
				interview_type, round_designation
			)
		)

	interview = frappe.new_doc("Interview")
	interview.interview_type = interview_type
	interview.job_applicant = doc.name
	interview.designation = doc.designation
	interview.resume_link = doc.resume_link
	interview.job_opening = doc.job_title

	interviewers = get_interviewers(interview_type)
	for d in interviewers:
		interview.append("interview_details", {"interviewer": d.interviewer})

	return interview


@frappe.whitelist()
def schedule_interview(
	job_applicant: str,
	interview_type: str,
	scheduled_on: str,
	from_time: str | None = None,
	to_time: str | None = None,
	interviewers: str | list | None = None,
) -> str:
	frappe.has_permission("Interview", ptype="create", throw=True)

	applicant = frappe.get_doc("Job Applicant", job_applicant)

	round_designation = frappe.db.get_value("Interview Type", interview_type, "designation")
	if round_designation and applicant.designation and round_designation != applicant.designation:
		frappe.throw(
			_("Interview Type {0} is only applicable for Designation {1}").format(
				frappe.bold(interview_type), frappe.bold(round_designation)
			)
		)

	interview = frappe.new_doc("Interview")
	interview.interview_type = interview_type
	interview.job_applicant = applicant.name
	interview.designation = applicant.designation
	interview.resume_link = applicant.resume_link
	interview.job_opening = applicant.job_title
	interview.scheduled_on = scheduled_on
	interview.from_time = from_time
	interview.to_time = to_time

	if isinstance(interviewers, str):
		interviewers = json.loads(interviewers)

	for entry in interviewers or []:
		if entry.get("interviewer"):
			interview.append("interview_details", {"interviewer": entry["interviewer"]})

	interview.insert(ignore_permissions=True)
	send_interview_invitation(interview, applicant)
	send_interview_scheduled_notification(interview, applicant)

	return interview.name


def send_interview_invitation(interview, applicant) -> None:
	from frappe.contacts.doctype.address.address import get_company_address

	settings = frappe.get_cached_doc("HR Settings")
	template_name = settings.get("interview_reminder_template")
	sender = settings.get("hiring_sender_email") or None

	interviewers = [d.interviewer for d in interview.interview_details]
	if not interviewers and not applicant.email_id:
		return

	context = interview.as_dict()
	context["applicant_name"] = applicant.applicant_name
	company = frappe.db.get_default("company")
	context["company"] = company
	context["company_address"] = get_company_address(company).get("company_address_display") or ""

	if template_name:
		template = frappe.get_doc("Email Template", template_name)
		subject = frappe.render_template(template.subject, context)
		body = template.response_html if template.use_html else template.response
		message = frappe.render_template(body, context)
	else:
		subject = _("Interview Scheduled: {0} on {1}").format(
			interview.interview_type, interview.scheduled_on
		)
		message = _("Your interview for {0} has been scheduled on {1}.").format(
			interview.interview_type, interview.scheduled_on
		)

	try:
		if interviewers:
			interviewer_context = dict(context, show_interview_link=True)
			interviewer_message = (
				frappe.render_template(body, interviewer_context) if template_name else message
			)
			frappe.sendmail(
				recipients=interviewers,
				sender=sender,
				subject=subject,
				message=interviewer_message,
				reference_doctype="Interview",
				reference_name=interview.name,
			)

		if applicant.email_id:
			frappe.sendmail(
				recipients=[applicant.email_id],
				sender=sender,
				subject=subject,
				message=message,
				reference_doctype="Interview",
				reference_name=interview.name,
			)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Interview Invitation Email Failed")
		frappe.msgprint(
			_(
				"Interview scheduled but invitation email could not be sent. "
				"Please configure your email account in HR Settings."
			),
			indicator="orange",
			alert=True,
		)


def send_interview_scheduled_notification(interview, applicant) -> None:
	from frappe.desk.doctype.notification_log.notification_log import make_notification_logs

	applicant_name = applicant.applicant_name
	subject = _("You have been assigned to interview {0} on {1}").format(
		applicant_name, interview.scheduled_on
	)
	notification = frappe._dict(
		type="Alert",
		document_type="Interview",
		document_name=interview.name,
		subject=subject,
		from_user=frappe.session.user,
	)
	interviewers = [d.interviewer for d in interview.interview_details]
	make_notification_logs(notification, interviewers)


@frappe.whitelist()
def send_feedback_pending_notification(interview_name: str) -> None:
	from frappe.desk.doctype.notification_log.notification_log import make_notification_logs

	from hrms.hr.doctype.interview.interview import get_recipients

	frappe.has_permission("Interview", "write", throw=True)

	pending = get_recipients(interview_name, for_feedback=1)
	if not pending:
		return

	interview = frappe.get_doc("Interview", interview_name)
	applicant_name = frappe.db.get_value("Job Applicant", interview.job_applicant, "applicant_name")
	subject = _("Please submit your feedback for {0}'s {1} interview").format(
		applicant_name, interview.interview_type
	)

	make_notification_logs(
		frappe._dict(
			type="Alert",
			document_type="Interview",
			document_name=interview_name,
			subject=subject,
			from_user=frappe.session.user,
		),
		pending,
	)

	settings = frappe.get_cached_doc("HR Settings")

	try:
		if settings.feedback_reminder_notification_template:
			template = frappe.get_doc(
				"Email Template", settings.feedback_reminder_notification_template
			)
			body = template.response_html if template.use_html else template.response
			context = interview.as_dict()
			context["applicant_name"] = applicant_name
			message = frappe.render_template(body, context)
		else:
			message = subject

		frappe.sendmail(
			recipients=pending,
			sender=settings.hiring_sender_email or None,
			subject=subject,
			message=message,
			reference_doctype="Interview",
			reference_name=interview_name,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Interview Feedback Reminder Email Failed")


@frappe.whitelist()
def get_interview_details(job_applicant: str) -> dict:
	interviews = frappe.db.get_all(
		"Interview",
		filters={"job_applicant": job_applicant, "docstatus": ["!=", 2]},
		fields=["name", "interview_type", "scheduled_on", "from_time", "to_time", "status", "average_rating"],
		order_by="scheduled_on asc, creation asc",
	)
	if not interviews:
		return None

	interview_names = [i.name for i in interviews]

	assigned = frappe.db.get_all(
		"Interview Detail",
		filters={"parent": ["in", interview_names]},
		fields=["parent", "interviewer"],
		order_by="idx asc",
	)

	submitted_feedbacks = frappe.db.get_all(
		"Interview Feedback",
		filters={"interview": ["in", interview_names], "docstatus": 1},
		fields=["interview", "interviewer", "average_rating", "name"],
	)

	feedback_map = {(f.interview, f.interviewer): f for f in submitted_feedbacks}

	details_map = {}
	for detail in assigned:
		details_map.setdefault(detail.parent, []).append(detail.interviewer)

	all_interviewers = list({detail.interviewer for detail in assigned})
	user_name_map = {}
	if all_interviewers:
		user_name_map = {
			u.name: u.full_name
			for u in frappe.db.get_all(
				"User",
				filters={"name": ["in", all_interviewers]},
				fields=["name", "full_name"],
			)
		}

	rounds = []
	for interview in interviews:
		interviewers_data = []
		for interviewer in details_map.get(interview.name, []):
			feedback = feedback_map.get((interview.name, interviewer))
			interviewers_data.append(
				frappe._dict(
					interviewer=interviewer,
					interviewer_name=user_name_map.get(interviewer, interviewer),
					feedback_submitted=bool(feedback),
					feedback_rating=flt((feedback.average_rating or 0) * 5, 1) if feedback else None,
					feedback_name=feedback.name if feedback else None,
				)
			)
		interview.average_rating = flt(interview.average_rating * 5, 1) if interview.average_rating else 0
		interview.interviewers = interviewers_data
		interview.feedback_count = sum(1 for i in interviewers_data if i.feedback_submitted)
		rounds.append(interview)

	return {"rounds": rounds}


@frappe.whitelist()
def get_applicant_to_hire_percentage() -> dict:
	frappe.has_permission("Job Applicant", throw=True)

	total_applicants = frappe.db.count("Job Applicant")
	total_hired = frappe.db.count("Job Applicant", filters={"status": "Accepted"})

	return {
		"value": flt(total_hired) / flt(total_applicants) * 100 if total_applicants else 0,
		"fieldtype": "Percent",
	}
