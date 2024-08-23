# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.functions import Avg
from frappe.utils import flt, get_link_to_form, getdate


class InterviewFeedback(Document):
	def validate(self):
		self.validate_interviewer()
		self.validate_interview_date()
		self.validate_duplicate()
		self.calculate_average_rating()

	def on_submit(self):
		self.update_interview_average_rating()

	def on_cancel(self):
		self.update_interview_average_rating()

	def validate_interviewer(self):
		applicable_interviewers = get_applicable_interviewers(self.interview)
		if self.interviewer not in applicable_interviewers:
			frappe.throw(
				_("{0} is not allowed to submit Interview Feedback for the Interview: {1}").format(
					frappe.bold(self.interviewer), frappe.bold(self.interview)
				)
			)

	def validate_interview_date(self):
		scheduled_date = frappe.db.get_value("Interview", self.interview, "scheduled_on")

		if getdate() < getdate(scheduled_date) and self.docstatus == 1:
			frappe.throw(
				_("Submission of {0} before {1} is not allowed").format(
					frappe.bold(_("Interview Feedback")), frappe.bold(_("Interview Scheduled Date"))
				)
			)

	def validate_duplicate(self):
		duplicate_feedback = frappe.db.exists(
			"Interview Feedback",
			{"interviewer": self.interviewer, "interview": self.interview, "docstatus": 1},
		)

		if duplicate_feedback:
			frappe.throw(
				_(
					"Feedback already submitted for the Interview {0}. Please cancel the previous Interview Feedback {1} to continue."
				).format(self.interview, get_link_to_form("Interview Feedback", duplicate_feedback))
			)

	def calculate_average_rating(self):
		total_rating = 0
		for d in self.skill_assessment:
			if d.rating:
				total_rating += flt(d.rating)

		self.average_rating = flt(
			total_rating / len(self.skill_assessment) if len(self.skill_assessment) else 0
		)

	def update_interview_average_rating(self):
		interview_feedback = frappe.qb.DocType("Interview Feedback")
		query = (
			frappe.qb.from_(interview_feedback)
			.where((interview_feedback.interview == self.interview) & (interview_feedback.docstatus == 1))
			.select(Avg(interview_feedback.average_rating).as_("average"))
		)
		data = query.run(as_dict=True)
		average_rating = data[0].average

		interview = frappe.get_doc("Interview", self.interview)
		interview.db_set("average_rating", average_rating)
		interview.notify_update()


@frappe.whitelist()
def get_applicable_interviewers(interview: str) -> list[str]:
	return frappe.get_all("Interview Detail", filters={"parent": interview}, pluck="interviewer")
