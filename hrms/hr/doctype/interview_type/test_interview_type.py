# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.permissions import add_user_permission

from hrms.hr.doctype.interview.test_interview import create_interview_type
from hrms.hr.doctype.interview_type.interview_type import (
	DEFAULT_INTERVIEW_TYPES,
	DEFAULT_SKILLS,
	create_default_types,
	create_interview,
)
from hrms.tests.utils import HRMSTestSuite, make_user


class TestInterviewType(HRMSTestSuite):
	def test_create_interview_permission(self):
		employee_user = make_user("test_interview_type_employee@example.com", "Employee")
		interviewer = make_user("test_interviewer1@example.com", "Interviewer")
		technical_round = create_interview_type("Technical Round", ["Python"], [interviewer])
		hr_round = create_interview_type("HR Round", ["Communication"], [interviewer])
		add_user_permission("Interview Type", hr_round.name, interviewer)

		with self.set_user(employee_user):
			self.assertRaises(frappe.PermissionError, create_interview, hr_round.name)

		with self.set_user(interviewer):
			self.assertRaises(frappe.PermissionError, create_interview, technical_round.name)

			interview = create_interview(hr_round.name)
			self.assertEqual(interview.interview_type, hr_round.name)
			self.assertEqual(interview.interview_details[0].interviewer, interviewer)

	def test_default_types_are_created_once_on_empty_site(self):
		delete_interview_types()
		frappe.db.delete("Skill", {"name": "Ownership"})

		create_default_types()
		create_default_types()

		self.assertCountEqual(frappe.get_all("Interview Type", pluck="name"), DEFAULT_INTERVIEW_TYPES)
		for skill in DEFAULT_SKILLS:
			self.assertEqual(frappe.db.count("Skill", {"name": skill}), 1)
		for name, (description, skills) in DEFAULT_INTERVIEW_TYPES.items():
			interview_type = frappe.get_doc("Interview Type", name)
			self.assertEqual(interview_type.description, description)
			self.assertEqual([row.skill for row in interview_type.expected_skill_set], skills)

	def test_default_types_skip_site_with_own_types(self):
		delete_interview_types()
		create_interview_type("Panel", ["Python"], [])

		create_default_types()

		self.assertEqual(frappe.get_all("Interview Type", pluck="name"), ["Panel"])


def delete_interview_types():
	"""Empties Interview Type with its child rows, so a recreated type does not load stale rows."""
	frappe.db.delete("Interview Type")
	frappe.db.delete("Expected Skill Set", {"parenttype": "Interview Type"})
	frappe.db.delete("Interviewer", {"parenttype": "Interview Type"})
