# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, add_months, get_first_day, get_year_ending, get_year_start, getdate

from hrms.hr.doctype.leave_application.test_leave_application import get_employee, get_leave_period
from hrms.hr.doctype.leave_period.test_leave_period import create_leave_period
from hrms.hr.doctype.leave_policy.test_leave_policy import create_leave_policy
from hrms.hr.doctype.leave_policy_assignment.leave_policy_assignment import (
	create_assignment,
	create_assignment_for_multiple_employees,
)
from hrms.hr.doctype.leave_type.test_leave_type import create_leave_type
from hrms.tests.utils import HRMSTestSuite


class TestLeavePolicyAssignment(HRMSTestSuite):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.make_employees()

	def setUp(self):
		for doctype in [
			"Leave Period",
			"Leave Application",
			"Leave Allocation",
			"Leave Policy",
			"Leave Policy Assignment",
			"Leave Ledger Entry",
		]:
			frappe.db.delete(doctype)

		employee = get_employee()
		self.original_doj = employee.date_of_joining
		self.employee = employee

	def tearDown(self):
		frappe.db.set_value("Employee", self.employee.name, "date_of_joining", self.original_doj)

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

	# tests no of leaves for passed months if assignment is based on Leave Period / Joining Date
	def test_get_leaves_for_passed_months(self):
		first_day = get_first_day(getdate())
		annual_allocation = 10
		leave_type = create_leave_type(
			leave_type_name="_Test Earned Leave", is_earned_leave=True, allocate_on_day="First Day"
		)
		leave_policy = create_leave_policy(leave_type=leave_type.name, annual_allocation=annual_allocation)
		leave_policy.submit()

		data = {
			"assignment_based_on": "Joining Date",
			"leave_policy": leave_policy.name,
		}

		self.employee.date_of_joining = add_months(first_day, -5)
		self.employee.save()
		assignment = create_assignment(self.employee.name, frappe._dict(data))
		new_leaves_allocated = assignment.get_leaves_for_passed_period(
			annual_allocation, leave_type, self.employee.date_of_joining
		)
		self.assertEqual(new_leaves_allocated, 5)

		self.employee.date_of_joining = add_months(first_day, -35)
		self.employee.save()
		assignment = create_assignment(self.employee.name, frappe._dict(data))
		new_leaves_allocated = assignment.get_leaves_for_passed_period(
			annual_allocation, leave_type, self.employee.date_of_joining
		)
		self.assertEqual(new_leaves_allocated, 30)

		leave_period = create_leave_period(add_months(first_day, -23), first_day)
		data = {
			"assignment_based_on": "Leave Period",
			"leave_policy": leave_policy.name,
			"leave_period": leave_period.name,
		}
		assignment = create_assignment(self.employee.name, frappe._dict(data))
		new_leaves_allocated = assignment.get_leaves_for_passed_period(
			annual_allocation, leave_type, self.employee.date_of_joining
		)
		self.assertEqual(new_leaves_allocated, 20)

	def test_pro_rated_leave_allocation_for_custom_date_range(self):
		leave_type = frappe.get_doc(
			{
				"doctype": "Leave Type",
				"leave_type_name": "_Test Leave Type_",
				"include_holiday": 1,
				"is_earned_leave": 1,
				"allocate_on_day": "First Day",
			}
		).submit()

		leave_policy = frappe.get_doc(
			{
				"doctype": "Leave Policy",
				"title": "Test Leave Policy",
				"leave_policy_details": [
					{
						"leave_type": leave_type.name,
						"annual_allocation": 12,
					}
				],
			}
		).submit()

		today_date = getdate()

		leave_policy_assignment = frappe.new_doc("Leave Policy Assignment")
		leave_policy_assignment.employee = self.employee.name
		leave_policy_assignment.leave_policy = leave_policy.name
		leave_policy_assignment.effective_from = getdate(get_first_day(today_date))
		leave_policy_assignment.effective_to = getdate(get_year_ending(today_date))
		leave_policy_assignment.submit()

		new_leaves_allocated = frappe.db.get_value(
			"Leave Allocation",
			{
				"employee": leave_policy_assignment.employee,
				"leave_policy_assignment": leave_policy_assignment.name,
			},
			"new_leaves_allocated",
		)

		self.assertGreater(new_leaves_allocated, 0)

	def test_earned_leave_allocation_if_leave_policy_assignment_submitted_after_period(self):
		year_start_date = get_year_start(getdate())
		year_end_date = get_year_ending(getdate())
		leave_period = create_leave_period(year_start_date, year_end_date)

		# assignment 10 days after the leave period
		frappe.flags.current_date = add_days(year_end_date, 10)
		leave_type = create_leave_type(
			leave_type_name="_Test Earned Leave", is_earned_leave=True, allocate_on_day="Last Day"
		)
		annual_earned_leaves = 10
		leave_policy = create_leave_policy(leave_type=leave_type.name, annual_allocation=annual_earned_leaves)
		leave_policy.submit()

		data = {
			"assignment_based_on": "Leave Period",
			"leave_policy": leave_policy.name,
			"leave_period": leave_period.name,
		}
		assignment = create_assignment(self.employee.name, frappe._dict(data))
		assignment.submit()

		earned_leave_allocation = frappe.get_value(
			"Leave Allocation", {"leave_policy_assignment": assignment.name}, "new_leaves_allocated"
		)
		self.assertEqual(earned_leave_allocation, annual_earned_leaves)

	def test_earned_leave_allocation_for_leave_period_spanning_two_years(self):
		first_year_start_date = get_year_start(getdate())
		second_year_end_date = get_year_ending(add_months(first_year_start_date, 12))
		leave_period = create_leave_period(first_year_start_date, second_year_end_date)

		# assignment during mid second year
		frappe.flags.current_date = add_months(second_year_end_date, -6)
		leave_type = create_leave_type(
			leave_type_name="_Test Earned Leave", is_earned_leave=True, allocate_on_day="Last Day"
		)
		annual_earned_leaves = 24
		leave_policy = create_leave_policy(leave_type=leave_type.name, annual_allocation=annual_earned_leaves)
		leave_policy.submit()

		data = {
			"assignment_based_on": "Leave Period",
			"leave_policy": leave_policy.name,
			"leave_period": leave_period.name,
		}
		assignment = create_assignment(self.employee.name, frappe._dict(data))
		assignment.submit()

		earned_leave_allocation = frappe.get_value(
			"Leave Allocation", {"leave_policy_assignment": assignment.name}, "new_leaves_allocated"
		)
		# months passed (18) are calculated correctly but total allocation of 36 exceeds 24 hence 24
		# this upper cap is intentional, without that 36 leaves would be allocated correctly
		self.assertEqual(earned_leave_allocation, 24)

	def test_skip_zero_allocation_leaves(self):
		today = getdate()
		leave_period = create_leave_period(get_year_start(today), get_year_ending(today))

		sick = create_leave_type(
			leave_type_name="_Test Sick Leave", non_encashable_leaves=0, max_leaves_allowed=2
		)
		casual = create_leave_type(
			leave_type_name="_Test Casual Leave", non_encashable_leaves=0, max_leaves_allowed=12
		)
		annual = create_leave_type(
			leave_type_name="_Test Annual Leave", non_encashable_leaves=0, max_leaves_allowed=27
		)
		compoff = create_leave_type(
			leave_type_name="_Test Comp Off", non_encashable_leaves=0, max_leaves_allowed=26
		)
		leave_policy = frappe.get_doc(
			{
				"doctype": "Leave Policy",
				"title": "Test Zero allocation Policy",
				"leave_policy_details": [
					{"leave_type": sick.name, "annual_allocation": 2},
					{"leave_type": casual.name, "annual_allocation": 2},
					{"leave_type": annual.name, "annual_allocation": 27},
					{"leave_type": compoff.name, "annual_allocation": 26},
				],
			}
		).submit()

		self.employee.date_of_joining = add_days(leave_period.to_date, -45)
		self.employee.save()

		assignment = create_assignment(
			self.employee.name,
			frappe._dict(
				{
					"assignment_based_on": "Leave Period",
					"leave_policy": leave_policy.name,
					"leave_period": leave_period.name,
				}
			),
		)
		assignment.submit()

		comments = frappe.get_all(
			"Comment",
			filters={
				"reference_doctype": "Leave Policy Assignment",
				"reference_name": assignment.name,
			},
			fields=["content"],
		)

		self.assertEqual(len(comments), 2)
		self.assertIn(casual.name, comments[0]["content"])
		self.assertIn(sick.name, comments[1]["content"])

		allocations = frappe.get_all(
			"Leave Allocation",
			filters={"leave_policy_assignment": assignment.name},
			fields=["leave_type", "new_leaves_allocated"],
		)

		self.assertEqual(allocations[0]["leave_type"], compoff.name)
		self.assertEqual(allocations[0]["new_leaves_allocated"], 3)
		self.assertEqual(allocations[1]["leave_type"], annual.name)
		self.assertEqual(allocations[1]["new_leaves_allocated"], 3)
