# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.permissions import add_user_permission

from hrms.hr.doctype.interview.test_interview import create_interview_type
from hrms.hr.doctype.interview_type.interview_type import create_interview
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
