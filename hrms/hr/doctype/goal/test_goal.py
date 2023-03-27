# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.appraisal_template.test_appraisal_template import create_kras
from hrms.hr.doctype.goal.goal import get_children


class TestGoal(FrappeTestCase):
	def setUp(self):
		frappe.db.delete("Goal")
		create_kras(["Development", "Quality"])

		self.employee1 = make_employee("employee1@example.com", company="_Test Company")
		self.employee2 = make_employee("employee2@example.com", company="_Test Company")

	def test_validate_parent_fields(self):
		parent_goal = create_goal(self.employee1, "Development", 1)
		child_goal = frappe.get_doc(
			{
				"doctype": "Goal",
				"goal_name": "Test",
				"employee": self.employee2,
				"kra": "Development",
				"parent_goal": parent_goal.name,
				"start_date": "2023-01-01",
			}
		)

		# parent goal and child goal should have same employee
		self.assertRaises(frappe.ValidationError, child_goal.insert)

	def test_set_status(self):
		goal = create_goal(self.employee1, "Development")
		self.assertEqual(goal.status, "Pending")

		goal.progress = 50
		goal.save()
		self.assertEqual(goal.status, "In Progress")

		goal.progress = 100
		goal.save()
		self.assertEqual(goal.status, "Completed")

	def test_update_parent_progress(self):
		parent_goal = create_goal(self.employee1, "Development", 1)
		child_goal1 = create_goal(self.employee1, parent_goal=parent_goal.name)
		child_goal2 = create_goal(self.employee1, parent_goal=parent_goal.name)

		child_goal1.progress = 50
		child_goal1.save()
		parent_goal.reload()
		self.assertEqual(parent_goal.progress, 25)

		child_goal2.progress = 100
		child_goal2.save()
		parent_goal.reload()
		self.assertEqual(parent_goal.progress, 75)

	def test_update_parent_progress_on_goal_deletion(self):
		parent_goal = create_goal(self.employee1, "Development", 1)
		child_goal1 = create_goal(self.employee1, parent_goal=parent_goal.name)
		child_goal2 = create_goal(self.employee1, parent_goal=parent_goal.name)

		child_goal1.progress = 50
		child_goal1.save()
		parent_goal.reload()
		self.assertEqual(parent_goal.progress, 25)

		child_goal2.delete()
		parent_goal.reload()
		self.assertEqual(parent_goal.progress, 50)

	def test_update_parent_progress_with_nested_goals(self):
		"""
		parent (12.5%)
		|_ child1
		|_ child2 (25%)
		        |_ child3 (50%)
		        |_ child4
		"""
		parent_goal = create_goal(self.employee1, "Development", 1)
		child_goal1 = create_goal(self.employee1, parent_goal=parent_goal.name)

		child_goal2 = create_goal(self.employee1, "Development", 1, parent_goal.name)
		child_goal3 = create_goal(self.employee1, parent_goal=child_goal2.name)
		child_goal4 = create_goal(self.employee1, parent_goal=child_goal2.name)

		child_goal3.progress = 50
		child_goal3.save()

		child_goal2.reload()
		self.assertEqual(child_goal2.progress, 25)

		parent_goal.reload()
		self.assertEqual(parent_goal.progress, 12.5)

	def test_update_old_parent_progress(self):
		"""
		BEFORE
		parent1 (12.5%)
		|_ child1 (12.5%)
		        |_ child1_1 (25%)
		        |_ child1_2

		parent2 (25%)
		|_ child2 (25%)
		        |_ child2_1 (50%)
		        |_ child2_2

		AFTER
		parent1 (16.667%)
		|_ child1 (16.667%)
		        |_ child1_1 (25%)
		        |_ child1_2
		        |_ child2 (25%)
		                |_ child2_1 (50%)
		                |_ child2_2

		parent2 (0%)
		"""
		parent1 = create_goal(self.employee1, "Development", 1)
		child1 = create_goal(self.employee1, is_group=1, parent_goal=parent1.name)
		child1_1 = create_goal(self.employee1, parent_goal=child1.name)
		child1_2 = create_goal(self.employee1, parent_goal=child1.name)

		parent2 = create_goal(self.employee1, "Development", 1)
		child2 = create_goal(self.employee1, is_group=1, parent_goal=parent2.name)
		child2_1 = create_goal(self.employee1, parent_goal=child2.name)
		child2_2 = create_goal(self.employee1, parent_goal=child2.name)

		child1_1.progress = 25
		child1_1.save()
		child1.reload()

		parent1.reload()
		self.assertEqual(child1.progress, 12.5)
		self.assertEqual(parent1.progress, 12.5)

		child2_1.progress = 50
		child2_1.save()
		child2.reload()
		parent2.reload()
		self.assertEqual(child2.progress, 25)
		self.assertEqual(parent2.progress, 25)

		child2.parent_goal = child1.name
		child2.save()
		parent2.reload()
		child1.reload()
		parent1.reload()

		self.assertEqual(parent2.progress, 0.0)
		self.assertEqual(child1.progress, 16.667)
		self.assertEqual(parent1.progress, 16.667)

	def test_update_kra_in_child_goals(self):
		parent_goal = create_goal(self.employee1, "Development", 1)
		child_goal1 = create_goal(self.employee1, parent_goal=parent_goal.name)
		child_goal2 = create_goal(self.employee1, parent_goal=parent_goal.name)

		parent_goal.reload()
		parent_goal.kra = "Quality"
		parent_goal.save()

		child_goal1.reload()
		child_goal2.reload()

		self.assertEqual(child_goal1.kra, "Quality")
		self.assertEqual(child_goal2.kra, "Quality")


def create_goal(
	employee,
	kra=None,
	is_group=0,
	parent_goal=None,
	appraisal_cycle=None,
	progress=0,
):
	return frappe.get_doc(
		{
			"doctype": "Goal",
			"goal_name": "Test",
			"employee": employee,
			"kra": kra,
			"is_group": is_group,
			"parent_goal": parent_goal,
			"start_date": "2023-01-01",
			"appraisal_cycle": appraisal_cycle,
			"progress": progress,
		}
	).insert()
