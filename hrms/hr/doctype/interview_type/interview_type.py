# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import json

import frappe
from frappe.model.document import Document

DEFAULT_SKILLS = ["Communication", "Role knowledge", "Problem solving", "Ownership", "Teamwork", "Leadership"]
DEFAULT_INTERVIEW_TYPES = {
	"Screening": (
		"First conversation to check interest, basics and fit for the role.",
		["Communication", "Role knowledge"],
	),
	"Technical": (
		"In-depth assessment of the skills the role needs.",
		["Role knowledge", "Problem solving"],
	),
	"Culture fit": (
		"How the candidate works with others and owns their work.",
		["Communication", "Teamwork", "Ownership"],
	),
	"Final": (
		"Closing conversation with the hiring manager or leadership.",
		["Communication", "Ownership", "Leadership"],
	),
}


class InterviewType(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		description: DF.Text | None
	# end: auto-generated types

	pass


@frappe.whitelist(methods=["POST"])
def create_interview(docname: str) -> Document:
	frappe.has_permission("Interview", ptype="create", throw=True)
	frappe.has_permission("Interview Type", ptype="read", doc=docname, throw=True)

	interview_type = frappe.get_doc("Interview Type", docname)

	interview = frappe.new_doc("Interview")
	interview.interview_type = interview_type.name
	interview.designation = interview_type.designation

	if interview_type.interviewers:
		interview.interview_details = []
		for d in interview_type.interviewers:
			interview.append("interview_details", {"interviewer": d.user})

	return interview


def create_default_types() -> None:
	"""Ship the standard interview rounds and their skills, for sites that have no Interview Type yet."""
	if frappe.db.count("Interview Type"):
		return

	for skill in DEFAULT_SKILLS:
		if not frappe.db.exists("Skill", skill):
			frappe.get_doc({"doctype": "Skill", "skill_name": skill}).insert(ignore_permissions=True)

	for name, (description, skills) in DEFAULT_INTERVIEW_TYPES.items():
		frappe.get_doc(
			{
				"doctype": "Interview Type",
				"interview_type_name": name,
				"description": description,
				"expected_skill_set": [{"skill": skill} for skill in skills],
			}
		).insert(ignore_permissions=True)
