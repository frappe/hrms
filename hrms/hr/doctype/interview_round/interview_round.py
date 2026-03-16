# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import json

import frappe
from frappe.model.document import Document


class InterviewRound(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.expected_skill_set.expected_skill_set import ExpectedSkillSet
		from hrms.hr.doctype.interviewer.interviewer import Interviewer

		designation: DF.Link | None
		expected_average_rating: DF.Rating
		expected_skill_set: DF.Table[ExpectedSkillSet]
		interview_type: DF.Link | None
		interviewers: DF.TableMultiSelect[Interviewer]
		round_name: DF.Data
	# end: auto-generated types

	pass


@frappe.whitelist()
def create_interview(interview_round: str) -> Document:
	doc = frappe.get_doc("Interview Round", interview_round)

	interview = frappe.new_doc("Interview")
	interview.interview_round = doc.name
	interview.designation = doc.designation

	if doc.interviewers:
		interview.interview_details = []
		for d in doc.interviewers:
			interview.append("interview_details", {"interviewer": d.user})

	return interview
