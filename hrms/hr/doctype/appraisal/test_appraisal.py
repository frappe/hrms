# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from erpnext.setup.doctype.designation.test_designation import create_designation
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.appraisal_cycle.appraisal_cycle import get_appraisal_cycle_summary
from hrms.hr.doctype.appraisal_cycle.test_appraisal_cycle import create_appraisal_cycle
from hrms.hr.doctype.appraisal_template.test_appraisal_template import create_appraisal_template
from hrms.hr.doctype.employee_performance_feedback.test_employee_performance_feedback import (
	create_performance_feedback,
)
from hrms.hr.doctype.goal.test_goal import create_goal
from hrms.tests.test_utils import create_company


class TestAppraisal(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("Goal")
		frappe.db.delete("Appraisal")
		frappe.db.delete("Employee Performance Feedback")

		self.company = create_company("_Test Appraisal").name
		self.template = create_appraisal_template()

		engineer = create_designation(designation_name="Engineer")
		engineer.appraisal_template = self.template.name
		engineer.save()

		self.employee1 = make_employee(
			"test_appraisal1@example.com", company=self.company, designation="Engineer"
		)

	def test_validate_duplicate(self):
		cycle = create_appraisal_cycle(designation="Engineer")
		cycle.create_appraisals()

		appraisal = frappe.get_doc(
			{
				"doctype": "Appraisal",
				"employee": self.employee1,
				"appraisal_cycle": cycle.name,
			}
		)
		appraisal.set_appraisal_template()

		self.assertRaises(frappe.DuplicateEntryError, appraisal.insert)

	def test_manual_kra_rating(self):
		cycle = create_appraisal_cycle(designation="Engineer", kra_evaluation_method="Manual Rating")
		cycle.create_appraisals()

		appraisal = frappe.db.exists("Appraisal", {"appraisal_cycle": cycle.name, "employee": self.employee1})
		appraisal = frappe.get_doc("Appraisal", appraisal)

		# 30% weightage
		appraisal.goals[0].score = 5
		# 70% weightage
		appraisal.goals[1].score = 3
		appraisal.save()

		self.assertEqual(appraisal.goals[0].score_earned, 1.5)
		self.assertEqual(appraisal.goals[1].score_earned, 2.1)

		self.assertEqual(appraisal.total_score, 3.6)
		self.assertEqual(appraisal.final_score, 1.2)

	def test_final_score(self):
		cycle = create_appraisal_cycle(designation="Engineer", kra_evaluation_method="Manual Rating")
		cycle.create_appraisals()
		appraisal = self.setup_appraisal(cycle)

		self.assertEqual(appraisal.final_score, 3.767)

	def test_final_score_using_formula(self):
		cycle = create_appraisal_cycle(designation="Engineer", kra_evaluation_method="Manual Rating")
		cycle.update(
			{
				"calculate_final_score_based_on_formula": 1,
				"final_score_formula": "(goal_score + self_appraisal_score + average_feedback_score)/3 if self_appraisal_score else (goal_score + self_appraisal_score)/2",
			}
		)
		cycle.save()
		cycle.create_appraisals()

		appraisal = self.setup_appraisal(cycle)

		self.assertEqual(appraisal.final_score, 3.767)

	def setup_appraisal(self, cycle):
		appraisal = frappe.db.exists("Appraisal", {"appraisal_cycle": cycle.name, "employee": self.employee1})
		appraisal = frappe.get_doc("Appraisal", appraisal)

		# GOAL SCORE
		appraisal.goals[0].score = 5  # 30% weightage
		appraisal.goals[1].score = 3  # 70% weightage

		# SELF APPRAISAL SCORE
		ratings = appraisal.self_ratings
		ratings[0].rating = 0.8  # 70% weightage
		ratings[1].rating = 0.7  # 30% weightage

		appraisal.save()

		# FEEDBACK SCORE
		reviewer = make_employee("reviewer1@example.com", designation="Engineer")
		feedback = create_performance_feedback(
			self.employee1,
			reviewer,
			appraisal.name,
		)
		ratings = feedback.feedback_ratings
		ratings[0].rating = 0.8  # 70% weightage
		ratings[1].rating = 0.7  # 30% weightage
		feedback.submit()

		appraisal.reload()

		return appraisal

	def test_goal_score(self):
		"""
		parent1 (12.5%) (Quality)
		|_ child1 (12.5%)
		        |_ child1_1 (25%)
		        |_ child1_2

		parent2 (50%) (Development)
		|_ child2_1 (100%)
		|_ child2_2
		"""
		cycle = create_appraisal_cycle(designation="Engineer")
		cycle.create_appraisals()

		parent1 = create_goal(self.employee1, "Quality", 1, appraisal_cycle=cycle.name)
		child1 = create_goal(self.employee1, is_group=1, parent_goal=parent1.name)
		# child1_1
		create_goal(self.employee1, parent_goal=child1.name, progress=25)
		# child1_1
		create_goal(self.employee1, parent_goal=child1.name)

		parent2 = create_goal(self.employee1, "Development", 1, appraisal_cycle=cycle.name)
		# child2_1
		create_goal(self.employee1, parent_goal=parent2.name, progress=100)
		# child2_2
		create_goal(self.employee1, parent_goal=parent2.name)

		appraisal = frappe.db.exists("Appraisal", {"appraisal_cycle": cycle.name, "employee": self.employee1})
		appraisal = frappe.get_doc("Appraisal", appraisal)

		# Quality KRA, 30% weightage
		self.assertEqual(appraisal.appraisal_kra[0].goal_completion, 12.5)
		self.assertEqual(appraisal.appraisal_kra[0].goal_score, 3.75)

		# Development KRA, 70% weightage
		self.assertEqual(appraisal.appraisal_kra[1].goal_completion, 50)
		self.assertEqual(appraisal.appraisal_kra[1].goal_score, 35)

		self.assertEqual(appraisal.goal_score_percentage, 38.75)
		self.assertEqual(appraisal.total_score, 1.938)
		self.assertEqual(appraisal.final_score, 0.646)

	def test_goal_score_after_parent_goal_change(self):
		"""
		BEFORE
		parent1 (50%) (Quality)
		|_ child1 (50%)

		parent2 (25%) (Development)
		|_ child2_1 (50%)
		|_ child2_2

		AFTER
		parent1 (50%) (Quality)
		|_ child1 (50%)
		|_ child2_1 (50%)

		parent2 (0%) (Development)
		|_ child2_2
		"""
		cycle = create_appraisal_cycle(designation="Engineer")
		cycle.create_appraisals()

		parent1 = create_goal(self.employee1, "Quality", 1, appraisal_cycle=cycle.name)
		# child1
		create_goal(self.employee1, parent_goal=parent1.name, progress=50)

		parent2 = create_goal(self.employee1, "Development", 1, appraisal_cycle=cycle.name)
		child2_1 = create_goal(self.employee1, parent_goal=parent2.name, progress=50)
		# child2_2
		create_goal(self.employee1, parent_goal=parent2.name)

		appraisal = frappe.db.exists("Appraisal", {"appraisal_cycle": cycle.name, "employee": self.employee1})
		appraisal = frappe.get_doc("Appraisal", appraisal)

		# Quality KRA, 30% weightage
		self.assertEqual(appraisal.appraisal_kra[0].goal_completion, 50)
		self.assertEqual(appraisal.appraisal_kra[0].goal_score, 15)

		# Development KRA, 70% weightage
		self.assertEqual(appraisal.appraisal_kra[1].goal_completion, 25)
		self.assertEqual(appraisal.appraisal_kra[1].goal_score, 17.5)

		# Parent changed. Old parent's KRA score should be updated
		child2_1.parent_goal = parent1.name
		child2_1.save()
		appraisal.reload()

		# Quality KRA, 30% weightage
		self.assertEqual(appraisal.appraisal_kra[0].goal_completion, 50)
		self.assertEqual(appraisal.appraisal_kra[0].goal_score, 15)

		# Development KRA, 70% weightage
		self.assertEqual(appraisal.appraisal_kra[1].goal_completion, 0)
		self.assertEqual(appraisal.appraisal_kra[1].goal_score, 0)

	def test_goal_score_after_kra_change(self):
		cycle = create_appraisal_cycle(designation="Engineer")
		cycle.create_appraisals()

		goal = create_goal(self.employee1, "Quality", appraisal_cycle=cycle.name, progress=50)

		appraisal = frappe.db.exists("Appraisal", {"appraisal_cycle": cycle.name, "employee": self.employee1})
		appraisal = frappe.get_doc("Appraisal", appraisal)

		# Quality KRA, 30% weightage
		self.assertEqual(appraisal.appraisal_kra[0].goal_completion, 50)
		self.assertEqual(appraisal.appraisal_kra[0].goal_score, 15)

		goal.kra = "Development"
		goal.save()

		# goal completion should now contribute to Development KRA score, instead of Quality (row 1)
		appraisal.reload()
		self.assertEqual(appraisal.appraisal_kra[0].goal_completion, 0)
		self.assertEqual(appraisal.appraisal_kra[0].goal_score, 0)

		self.assertEqual(appraisal.appraisal_kra[1].goal_completion, 50)
		self.assertEqual(appraisal.appraisal_kra[1].goal_score, 35)

	def test_goal_score_after_goal_deletion(self):
		cycle = create_appraisal_cycle(designation="Engineer")
		cycle.create_appraisals()

		goal = create_goal(self.employee1, "Quality", appraisal_cycle=cycle.name, progress=50)

		appraisal = frappe.db.exists("Appraisal", {"appraisal_cycle": cycle.name, "employee": self.employee1})
		appraisal = frappe.get_doc("Appraisal", appraisal)

		# Quality KRA, 30% weightage
		self.assertEqual(appraisal.appraisal_kra[0].goal_completion, 50)
		self.assertEqual(appraisal.appraisal_kra[0].goal_score, 15)

		goal.delete()
		appraisal.reload()
		self.assertEqual(appraisal.appraisal_kra[0].goal_completion, 0)
		self.assertEqual(appraisal.appraisal_kra[0].goal_score, 0)

	def test_calculate_self_appraisal_score(self):
		cycle = create_appraisal_cycle(designation="Engineer")
		cycle.create_appraisals()

		appraisal = frappe.db.exists("Appraisal", {"appraisal_cycle": cycle.name, "employee": self.employee1})
		appraisal = frappe.get_doc("Appraisal", appraisal)

		ratings = appraisal.self_ratings
		# 70% weightage
		ratings[0].rating = 0.8
		# 30% weightage
		ratings[1].rating = 0.7

		appraisal.save()
		self.assertEqual(appraisal.self_score, 3.85)

	def test_cycle_completion(self):
		cycle = create_appraisal_cycle(designation="Engineer")
		cycle.create_appraisals()

		# unsubmitted appraisals
		self.assertRaises(frappe.ValidationError, cycle.complete_cycle)

		appraisal = frappe.db.exists("Appraisal", {"appraisal_cycle": cycle.name, "employee": self.employee1})
		appraisal = frappe.get_doc("Appraisal", appraisal)
		appraisal.submit()

		cycle.complete_cycle()
		appraisal = frappe.get_doc(
			{
				"doctype": "Appraisal",
				"employee": self.employee1,
				"appraisal_cycle": cycle.name,
				"appraisal_template": self.template.name,
			}
		)

		# transaction against a Completed cycle
		self.assertRaises(frappe.ValidationError, appraisal.insert)

	def test_cycle_summary(self):
		employee2 = make_employee("test_appraisal2@example.com", company=self.company, designation="Engineer")

		cycle = create_appraisal_cycle(designation="Engineer")
		cycle.create_appraisals()

		appraisal = frappe.db.exists("Appraisal", {"appraisal_cycle": cycle.name, "employee": self.employee1})
		appraisal = frappe.get_doc("Appraisal", appraisal)

		create_goal(self.employee1, "Quality", appraisal_cycle=cycle.name)
		feedback = create_performance_feedback(
			self.employee1,
			employee2,
			appraisal.name,
		)
		ratings = feedback.feedback_ratings
		ratings[0].rating = 0.8  # 70% weightage
		ratings[1].rating = 0.7  # 30% weightage
		feedback.submit()

		summary = get_appraisal_cycle_summary(cycle.name)

		expected_data = {
			"appraisees": 2,
			"self_appraisal_pending": 2,
			"goals_missing": 1,
			"feedback_missing": 1,
		}
		self.assertEqual(summary, expected_data)
