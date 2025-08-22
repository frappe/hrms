# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from erpnext.setup.doctype.designation.test_designation import create_designation
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.appraisal_cycle.test_appraisal_cycle import create_appraisal_cycle
from hrms.hr.doctype.appraisal_template.test_appraisal_template import create_appraisal_template
from hrms.tests.test_utils import create_company


class TestEmployeePerformanceFeedback(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("Employee Performance Feedback")
		frappe.db.delete("Appraisal")

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
		self.assertEqual(avg_feedback_score, 3.575)

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
