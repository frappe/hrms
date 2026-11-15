# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

# For license information, please see license.txt


import json
from collections import defaultdict

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.model.naming import append_number_if_name_exists
from frappe.utils import flt, validate_email_address

from hrms.hr.doctype.interview.interview import get_interviewers, has_interviews, stars_from_rating
from hrms.hr.page.hiring.hiring import is_not_cleared


class DuplicationError(frappe.ValidationError):
	pass


class JobApplicant(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

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
		rejection_note: DF.SmallText | None
		rejection_reason: DF.Link | None
		resume_attachment: DF.Attach | None
		resume_link: DF.Data | None
		source: DF.Link | None
		source_name: DF.Link | None
		stage: DF.Literal["Applied", "Shortlisted", "Interviewing", "Offered", "Hired", "Rejected"]
		status: DF.Literal["Open", "Replied", "Shortlisted", "Rejected", "Hold", "Accepted"]
		upper_range: DF.Currency
	# end: auto-generated types

	def onload(self):
		job_offer = frappe.get_all("Job Offer", filters={"job_applicant": self.name, "docstatus": ["!=", 2]})
		if job_offer:
			self.set_onload("job_offer", job_offer[0].name)

		employee = frappe.db.get_value("Employee", {"job_applicant": self.name}, "name") or ""
		self.set_onload("employee", employee)

	def autoname(self):
		self.name = self.email_id

		# applicant can apply more than once for a different job title or reapply
		if frappe.db.exists("Job Applicant", self.name):
			self.name = append_number_if_name_exists("Job Applicant", self.name)

	def validate(self):
		if self.email_id:
			validate_email_address(self.email_id, True)

		self.set_stage()
		self.set_status_for_stage()
		self.clear_rejection()

		if self.employee_referral:
			self.set_status_for_employee_referral()

		if not self.applicant_name and self.email_id:
			guess = self.email_id.split("@")[0]
			self.applicant_name = " ".join([p.capitalize() for p in guess.split(".")])

	def clear_rejection(self):
		"""The reason and note belong to a rejection; they go when the applicant is no longer rejected."""
		if self.status != "Rejected":
			self.rejection_reason = None
			self.rejection_note = None

	def set_stage(self):
		self.apply_manual_stage_move()
		self.stage = get_stage(self)

	def set_status_for_stage(self):
		self.status = get_status_for_stage(self.stage, self.status)

	@frappe.whitelist()
	def put_on_hold(self):
		self.check_permission("write")
		self.check_can_hold()
		self.status = "Hold"
		self.save()

	@frappe.whitelist()
	def resume(self):
		self.check_permission("write")
		if self.status != "Hold":
			return
		self.status = "Open" if self.stage == "Applied" else "Shortlisted"
		self.save()

	def check_can_hold(self):
		if self.stage in ("Rejected", "Hired"):
			frappe.throw(
				_("{0} is {1}, so they can't be put on hold.").format(
					self.applicant_name or self.name, self.stage
				),
				title=_("Not Allowed"),
			)

	def apply_manual_stage_move(self):
		"""Only Applied, Shortlisted and Rejected can be picked by hand (Kanban drag, list edit);
		Interviewing, Offered and Hired follow the interviews and offers."""
		previous = self.get_doc_before_save()
		previous_stage = previous.stage if previous else "Applied"

		if self.stage == previous_stage or self.stage == get_stage(self):
			return

		name = self.applicant_name or self.name

		if self.stage in FOLLOWS_RECORDS_STAGES:
			frappe.throw(get_follows_records_messages()[self.stage].format(name), title=_("Not Allowed"))

		self.status = STATUS_FOR_MANUAL_STAGE[self.stage]
		computed_stage = get_stage(self)

		if computed_stage != self.stage and previous_stage != "Rejected":
			frappe.throw(get_stay_in_stage_messages()[computed_stage].format(name), title=_("Not Allowed"))

	def before_insert(self):
		if self.job_title:
			job_opening = frappe.db.get_value(
				"Job Opening", self.job_title, ["status", "prevent_duplicate_applicant"], as_dict=True
			)
			if not job_opening:
				return

			if job_opening.status == "Closed":
				frappe.throw(_("This opening is closed to new applicants."), title=_("Not Allowed"))
			if job_opening.prevent_duplicate_applicant and self.email_id:
				if frappe.db.exists(
					"Job Applicant", {"email_id": self.email_id, "job_title": self.job_title}
				):
					frappe.throw(
						_("You have already applied for this position."),
						exc=DuplicationError,
						title=_("Duplicate Application"),
					)

		if frappe.flags.in_web_form and not self.source:
			self.source = "Website Listing"

	def set_status_for_employee_referral(self):
		emp_ref = frappe.get_doc("Employee Referral", self.employee_referral)
		if self.status in ["Open", "Replied", "Shortlisted", "Hold"]:
			emp_ref.db_set("status", "In Process")
		elif self.status in ["Accepted", "Rejected"]:
			emp_ref.db_set("status", self.status)


STATUS_FOR_MANUAL_STAGE = {"Applied": "Open", "Shortlisted": "Shortlisted", "Rejected": "Rejected"}

# Interviewing and Offered keep the status they had: Open or Shortlisted, both still true
STATUS_FOR_STAGE = {**STATUS_FOR_MANUAL_STAGE, "Hired": "Accepted"}

FOLLOWS_RECORDS_STAGES = ("Interviewing", "Offered", "Hired")


def get_follows_records_messages() -> dict[str, str]:
	return {
		"Interviewing": _("Schedule an interview to move {0} to Interviewing."),
		"Offered": _("Create a job offer to move {0} to Offered."),
		"Hired": _("Mark the job offer as accepted to move {0} to Hired."),
	}


def get_stay_in_stage_messages() -> dict[str, str]:
	return {
		"Interviewing": _(
			"{0} has an interview, so they stay in Interviewing. Cancel the interview to move them back."
		),
		"Offered": _("{0} has a job offer, so they stay in Offered. Cancel the offer to move them back."),
		"Hired": _("{0} is already hired, so they stay in Hired."),
	}


def get_status_for_stage(stage: str, status: str) -> str:
	"""The status that goes with a stage. Hold stays until resumed; Interviewing and Offered keep theirs."""
	if stage in ("Rejected", "Hired"):
		return STATUS_FOR_STAGE[stage]
	if status == "Hold" and stage in ("Applied", "Shortlisted", "Interviewing", "Offered"):
		return "Hold"
	return status


def get_stage(applicant: str | Document) -> str:
	"""The hiring stage an applicant is in; the first matching rule wins."""
	if isinstance(applicant, str):
		applicant = frappe.get_doc("Job Applicant", applicant)

	if applicant.status == "Rejected":
		return "Rejected"

	if has_accepted_offer(applicant.name) or frappe.db.exists("Employee", {"job_applicant": applicant.name}):
		return "Hired"

	# a draft offer counts: the candidate is at the offer stage while it is being prepared
	if frappe.db.exists(
		"Job Offer",
		{
			"job_applicant": applicant.name,
			"docstatus": ["<", 2],
			"status": ["not in", ["Rejected", "Cancelled", "Accepted"]],
		},
	):
		return "Offered"

	if has_interviews(applicant.name):
		return "Interviewing"

	if applicant.status in ("Shortlisted", "Accepted"):
		return "Shortlisted"

	# Hold keeps the stage it was put on hold in
	if (
		applicant.status == "Hold"
		and frappe.db.get_value("Job Applicant", applicant.name, "stage") == "Shortlisted"
	):
		return "Shortlisted"

	return "Applied"


def has_accepted_offer(applicant: str) -> bool:
	return bool(
		frappe.db.exists("Job Offer", {"job_applicant": applicant, "docstatus": 1, "status": "Accepted"})
	)


def update_stage(applicant: str | None):
	"""Store the stage after an interview, offer or employee changed, and refresh open lists."""
	if not applicant:
		return

	current = frappe.db.get_value("Job Applicant", applicant, ["status", "stage"], as_dict=True)
	if not current:
		return

	stage = get_stage(frappe._dict(name=applicant, status=current.status))
	status = get_status_for_stage(stage, current.status)
	if status != current.status:
		frappe.db.set_value("Job Applicant", applicant, "status", status, update_modified=False)
	if stage != current.stage:
		frappe.get_doc("Job Applicant", applicant).db_set("stage", stage, notify=True)


@frappe.whitelist()
def make_employee(source_name: str, target_doc: str | Document | None = None) -> Document:
	def set_missing_values(source, target):
		target.employee_name = source.applicant_name

		if not source.job_title:
			return

		job_opening = frappe.db.get_value(
			"Job Opening",
			source.job_title,
			["company", "department", "employment_type"],
			as_dict=True,
		)
		if not job_opening:
			return

		if job_opening.company:
			target.company = job_opening.company
		if job_opening.department:
			target.department = job_opening.department
		if job_opening.employment_type:
			target.employment_type = job_opening.employment_type

	return get_mapped_doc(
		"Job Applicant",
		source_name,
		{
			"Job Applicant": {
				"doctype": "Employee",
				"field_map": {
					"applicant_name": "first_name",
					"email_id": "personal_email",
					"phone_number": "cell_number",
					"currency": "salary_currency",
				},
				"field_no_map": ["status"],
			}
		},
		target_doc,
		set_missing_values,
	)


@frappe.whitelist(methods=["POST"])
def create_interview(job_applicant: str, interview_type: str) -> Document:
	frappe.has_permission("Interview", ptype="create", throw=True)
	frappe.has_permission("Job Applicant", ptype="read", doc=job_applicant, throw=True)

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


@frappe.whitelist(methods=["POST"])
def schedule_interview(
	job_applicant: str,
	interview_type: str,
	scheduled_on: str,
	from_time: str | None = None,
	to_time: str | None = None,
	interviewers: str | list | None = None,
) -> str:
	frappe.has_permission("Interview", ptype="create", throw=True)
	frappe.has_permission("Job Applicant", ptype="read", doc=job_applicant, throw=True)

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

	return interview.name


@frappe.whitelist()
def get_interview_details(job_applicant: str) -> list[dict] | None:
	"""The applicant's interviews, newest first, for the form's Interview Summary."""
	frappe.has_permission("Job Applicant", "read", job_applicant, throw=True)
	interviews = frappe.get_all(
		"Interview",
		filters={"job_applicant": job_applicant, "docstatus": ["!=", 2]},
		fields=["name", "interview_type", "scheduled_on", "from_time", "average_rating", "status"],
		order_by="scheduled_on desc, creation desc",
	)
	if not interviews:
		return None

	results = defaultdict(list)
	for row in frappe.get_all(
		"Interview Feedback",
		filters={"interview": ["in", [interview.name for interview in interviews]], "docstatus": 1},
		fields=["interview", "result"],
	):
		results[row.interview].append(row.result)

	for interview in interviews:
		interview.feedback_results = results[interview.name]
		interview.is_not_cleared = is_not_cleared(interview)
		interview.from_time = str(interview.from_time or "")
		interview.average_rating = stars_from_rating(interview.average_rating)
	return interviews


@frappe.whitelist()
def get_applicant_to_hire_percentage() -> dict:
	frappe.has_permission("Job Applicant", throw=True)

	total_applicants = frappe.db.count("Job Applicant")
	total_hired = frappe.db.count("Job Applicant", filters={"status": "Accepted"})

	return {
		"value": flt(total_hired) / flt(total_applicants) * 100 if total_applicants else 0,
		"fieldtype": "Percent",
	}
