# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import json

import frappe
from frappe.model.document import Document


class InterviewRound(Document):
	pass


@frappe.whitelist()
def create_interview(doc):
	if isinstance(doc, str):
		doc = json.loads(doc)
		doc = frappe.get_doc(doc)

	interview = frappe.new_doc("Interview")
	interview.interview_round = doc.name
	interview.designation = doc.designation

	if doc.interviewers:
		interview.interview_details = []
<<<<<<< HEAD
		for data in doc.interviewers:
			interview.append("interview_details", {"interviewer": data.user})
=======
		for d in doc.interviewers:
			interview.append("interview_details", {"interviewer": d.user})

>>>>>>> da17577dc (chore: remove unused import)
	return interview
