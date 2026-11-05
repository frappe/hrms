# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe

from erpnext.setup.doctype.designation.test_designation import create_designation
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.appraisal_cycle.test_appraisal_cycle import create_appraisal_cycle
from hrms.hr.doctype.appraisal_template.test_appraisal_template import create_appraisal_template
from hrms.tests.test_utils import create_company
from hrms.tests.utils import HRMSTestSuite


class TestEmployeePerformanceFeedback(HRMSTestSuite):
	def setUp(self):
		company = create_company("_Test Appraisal").name
		self.template = create_appraisal_template()

		engineer = create_designation(designation_name="Engineer")
		engineer.appraisal_template = self.template.name
		engineer.save()

		self.employee = make_employee("employee@example.com", company=company, designation="Engineer")
		self.reviewer1 = make_employee("reviewer1@example.com", company=company, designation="Engineer")
		self.reviewer2 = make_employee("reviewer2@example.com", company=company, designation="Engineer")

		cycle = create_appraisal_cycle(designation="Engineer")
		cycle.create_appraisals()

		self.appraisal = frappe.db.get_all("Appraisal", filters={"appraisal_cycle": cycle.name})[0].name

	def test_validate_employees(self):
		feedback = frappe.get_doc(
			{
				"doctype": "Employee Performance Feedback",
				"employee": self.employee,
				"reviewer": self.employee,
				"appraisal": self.appraisal,
			}
		)

		feedback.set_feedback_criteria()
		self.assertRaises(frappe.ValidationError, feedback.insert)

	def test_set_feedback_criteria(self):
		feedback = create_performance_feedback(
			self.employee,
			self.reviewer1,
			self.appraisal,
		)
		self.assertEqual(feedback.feedback_ratings[0].criteria, "Problem Solving")
		self.assertEqual(feedback.feedback_ratings[0].per_weightage, 70.0)
		self.assertEqual(feedback.feedback_ratings[1].criteria, "Excellence")
		self.assertEqual(feedback.feedback_ratings[1].per_weightage, 30.0)

	def test_set_total_score(self):
		feedback = create_performance_feedback(
			self.employee,
			self.reviewer1,
			self.appraisal,
		)

		ratings = feedback.feedback_ratings
		# 70% weightage
		ratings[0].rating = 0.8
		# 30% weightage
		ratings[1].rating = 0.7

		feedback.save()

		self.assertEqual(feedback.total_score, 3.85)

	def test_update_avg_feedback_score_in_appraisal(self):
		feedback1 = create_performance_feedback(
			self.employee,
			self.reviewer1,
			self.appraisal,
		)

		ratings = feedback1.feedback_ratings
		# 70% weightage
		ratings[0].rating = 0.8
		# 30% weightage
		ratings[1].rating = 0.7

		feedback1.submit()

		feedback2 = create_performance_feedback(
			self.employee,
			self.reviewer2,
			self.appraisal,
		)

		ratings = feedback2.feedback_ratings
		# 70% weightage
		ratings[0].rating = 0.6
		# 30% weightage
		ratings[1].rating = 0.8

		feedback2.submit()

		avg_feedback_score = frappe.db.get_value("Appraisal", self.appraisal, "avg_feedback_score")
		self.assertEqual(avg_feedback_score, 3.58)

	def test_update_avg_feedback_score_on_cancel(self):
		feedback = create_performance_feedback(
			self.employee,
			self.reviewer1,
			self.appraisal,
		)

		ratings = feedback.feedback_ratings
		# 70% weightage
		ratings[0].rating = 0.8
		# 30% weightage
		ratings[1].rating = 0.7
		feedback.submit()

		avg_feedback_score = frappe.db.get_value("Appraisal", self.appraisal, "avg_feedback_score")
		self.assertEqual(avg_feedback_score, 3.85)

		feedback.cancel()

		avg_feedback_score = frappe.db.get_value("Appraisal", self.appraisal, "avg_feedback_score")
		self.assertEqual(avg_feedback_score, 0.0)

	def test_reviewer_must_be_session_user(self):
		frappe.set_user("employee@example.com")
		try:
			feedback = frappe.get_doc(
				{
					"doctype": "Employee Performance Feedback",
					"employee": self.employee,
					"reviewer": self.reviewer1,
					"appraisal": self.appraisal,
					"feedback": "Test Feedback",
				}
			)
			feedback.set_feedback_criteria()
			self.assertRaises(frappe.PermissionError, feedback.insert)
		finally:
			frappe.set_user("Administrator")

	def test_appraisee_cannot_cancel_feedback(self):
		feedback = create_performance_feedback(self.employee, self.reviewer1, self.appraisal)
		feedback.submit()

		frappe.set_user("employee@example.com")
		try:
			feedback = frappe.get_doc("Employee Performance Feedback", feedback.name)
			self.assertRaises(frappe.PermissionError, feedback.cancel)
		finally:
			frappe.set_user("Administrator")

	def test_rating_is_bounded(self):
		feedback = create_performance_feedback(self.employee, self.reviewer1, self.appraisal)
		for row in feedback.feedback_ratings:
			row.rating = 5
		feedback.save()

		self.assertEqual(feedback.total_score, 5.0)

	def test_weightage_reset_from_template(self):
		feedback = create_performance_feedback(self.employee, self.reviewer1, self.appraisal)
		feedback.feedback_ratings[0].per_weightage = 0
		feedback.feedback_ratings[1].per_weightage = 100
		feedback.feedback_ratings[0].rating = 0.2
		feedback.feedback_ratings[1].rating = 1
		feedback.save()

		self.assertEqual(feedback.feedback_ratings[0].per_weightage, 70.0)
		self.assertEqual(feedback.feedback_ratings[1].per_weightage, 30.0)
		self.assertEqual(feedback.total_score, 2.2)


def create_performance_feedback(employee, reviewer, appraisal):
	feedback = frappe.get_doc(
		{
			"doctype": "Employee Performance Feedback",
			"employee": employee,
			"reviewer": reviewer,
			"appraisal": appraisal,
			"feedback": "Test Feedback",
		}
	)

	feedback.set_feedback_criteria()
	feedback.insert()

	return feedback
