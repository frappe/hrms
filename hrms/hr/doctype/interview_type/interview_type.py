# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import json

import frappe
from frappe.model.document import Document


class InterviewType(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		description: DF.Text | None
	# end: auto-generated types

	pass


@frappe.whitelist()
def create_interview(docname: str):
	interview_type = frappe.get_doc("Interview Type", docname)

	interview = frappe.new_doc("Interview")
	interview.interview_type = interview_type.name
	interview.designation = interview_type.designation

	if interview_type.interviewers:
		interview.interview_details = []
		for d in interview_type.interviewers:
			interview.append("interview_details", {"interviewer": d.user})

	return interview
