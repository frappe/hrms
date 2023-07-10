# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import unittest

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_months, get_first_day, getdate

from hrms.hr.doctype.leave_application.test_leave_application import get_employee, get_leave_period
from hrms.hr.doctype.leave_policy.test_leave_policy import create_leave_policy
from hrms.hr.doctype.leave_policy_assignment.leave_policy_assignment import (
	create_assignment_for_multiple_employees,
)

test_dependencies = ["Employee"]


class TestLeavePolicyAssignment(FrappeTestCase):
	def setUp(self):
		for doctype in [
			"Leave Period",
			"Leave Application",
			"Leave Allocation",
			"Leave Policy Assignment",
			"Leave Ledger Entry",
		]:
			frappe.db.delete(doctype)

		employee = get_employee()
		self.original_doj = employee.date_of_joining
		self.employee = employee

	def test_grant_leaves(self):
		leave_period = get_leave_period()
		leave_policy = create_leave_policy(annual_allocation=10)
		leave_policy.submit()

		self.employee.date_of_joining = get_first_day(leave_period.from_date)
		self.employee.save()

		data = frappe._dict(
			{
				"assignment_based_on": "Leave Period",
				"leave_policy": leave_policy.name,
				"leave_period": leave_period.name,
			}
		)
		assignments = create_assignment_for_multiple_employees([self.employee.name], data)
		self.assertEqual(
			frappe.db.get_value("Leave Policy Assignment", assignments[0], "leaves_allocated"),
			1,
		)

		allocation = frappe.db.get_value(
			"Leave Allocation", {"leave_policy_assignment": assignments[0]}, "name"
		)

		leave_alloc_doc = frappe.get_doc("Leave Allocation", allocation)

		self.assertEqual(leave_alloc_doc.new_leaves_allocated, 10)
		self.assertEqual(leave_alloc_doc.leave_type, "_Test Leave Type")
		self.assertEqual(getdate(leave_alloc_doc.from_date), getdate(leave_period.from_date))
		self.assertEqual(getdate(leave_alloc_doc.to_date), getdate(leave_period.to_date))
		self.assertEqual(leave_alloc_doc.leave_policy, leave_policy.name)
		self.assertEqual(leave_alloc_doc.leave_policy_assignment, assignments[0])

	def test_allow_to_grant_all_leave_after_cancellation_of_every_leave_allocation(self):
		leave_period = get_leave_period()
		leave_policy = create_leave_policy(annual_allocation=10)
		leave_policy.submit()

		data = frappe._dict(
			{
				"assignment_based_on": "Leave Period",
				"leave_policy": leave_policy.name,
				"leave_period": leave_period.name,
			}
		)
		assignments = create_assignment_for_multiple_employees([self.employee.name], data)

		# every leave is allocated no more leave can be granted now
		self.assertEqual(
			frappe.db.get_value("Leave Policy Assignment", assignments[0], "leaves_allocated"),
			1,
		)

		allocation = frappe.db.get_value(
			"Leave Allocation", {"leave_policy_assignment": assignments[0]}, "name"
		)

		leave_alloc_doc = frappe.get_doc("Leave Allocation", allocation)
		leave_alloc_doc.cancel()
		leave_alloc_doc.delete()
		self.assertEqual(
			frappe.db.get_value("Leave Policy Assignment", assignments[0], "leaves_allocated"),
			0,
		)

	def test_pro_rated_leave_allocation(self):
		leave_period = get_leave_period()
		leave_policy = create_leave_policy(annual_allocation=12)
		leave_policy.submit()

		self.employee.date_of_joining = add_months(leave_period.from_date, 3)
		self.employee.save()

		data = {
			"assignment_based_on": "Leave Period",
			"leave_policy": leave_policy.name,
			"leave_period": leave_period.name,
		}
		assignments = create_assignment_for_multiple_employees([self.employee.name], frappe._dict(data))

		allocation = frappe.db.get_value(
			"Leave Allocation", {"leave_policy_assignment": assignments[0]}, "new_leaves_allocated"
		)

		# pro-rated leave allocation for 9 months
		self.assertEqual(allocation, 9)

	def tearDown(self):
		frappe.db.set_value("Employee", self.employee.name, "date_of_joining", self.original_doj)
