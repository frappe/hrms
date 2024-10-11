# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import datetime

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, add_months, get_first_day, get_year_ending, get_year_start, getdate

from hrms.hr.doctype.leave_application.test_leave_application import (
	get_employee,
	get_leave_balance_on,
	get_leave_period,
)
from hrms.hr.doctype.leave_policy.test_leave_policy import create_leave_policy
from hrms.hr.doctype.leave_policy_assignment.leave_policy_assignment import (
	LeaveAcrossAllocationsMidPeriodError,
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
		leave_policy_assignment.employee = self.employee
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

	def test_mid_period_leave_policy_change(self):
		leave_type = frappe.get_doc(
			{
				"doctype": "Leave Type",
				"leave_type_name": "_Test Leave Type Mid Period Policy Change",
				"include_holiday": 1,
			}
		).insert()
		leave_policy_1 = create_leave_policy(annual_allocation=6, leave_type=leave_type.name).submit()
		leave_policy_2 = create_leave_policy(annual_allocation=12, leave_type=leave_type.name).submit()

		today_date = getdate()
		year_start = getdate(get_year_start(today_date))
		year_end = getdate(get_year_ending(today_date))
		leave_policy_assignment = create_leave_policy_assignment(
			self.employee.name,
			leave_policy_1.name,
			year_start,
			year_end,
		).submit()

		new_assignment_date = add_months(year_start, 6)
		new_leave_policy_assignment = create_leave_policy_assignment(
			self.employee.name,
			leave_policy_2.name,
			new_assignment_date,
			year_end,
		)
		new_leave_policy_assignment.mid_period_change = True

		new_leave_policy_assignment.submit()

		leave_allocation_name = frappe.db.exists(
			"Leave Allocation",
			{
				"leave_policy_assignment": leave_policy_assignment.name,
				"docstatus": 1,
			},
		)
		leave_allocation = frappe.get_doc("Leave Allocation", leave_allocation_name)
		leave_ledger_entry_to_date = frappe.db.get_value(
			"Leave Ledger Entry",
			{
				"transaction_name": leave_allocation_name,
				"docstatus": 1,
			},
			"to_date",
		)
		leave_policy_assignment = leave_policy_assignment.reload()
		end_date = add_days(new_leave_policy_assignment.effective_from, -1)

		self.assertEqual(getdate(leave_policy_assignment.effective_to), end_date)
		self.assertEqual(getdate(leave_allocation.to_date), end_date)
		self.assertEqual(getdate(leave_ledger_entry_to_date), end_date)
		self.assertEqual(
			get_leave_balance_on(self.employee.name, leave_type.name, add_days(new_assignment_date, 1)),
			12,
		)

	def test_leave_across_allocations_mid_period_leave_policy_change(self):
		employee = frappe.get_doc("Employee", "_T-Employee-00002")
		leave_type = frappe.get_doc(
			{
				"doctype": "Leave Type",
				"leave_type_name": "_Test Leave Type Across Mid Period Policy Change",
			}
		).insert()
		leave_policy_1 = create_leave_policy(leave_type=leave_type.name).submit()
		leave_policy_2 = create_leave_policy(eave_type=leave_type.name).submit()

		year_start = datetime.date(getdate().year + 1, 1, 1)
		year_end = getdate(get_year_ending(year_start))
		create_leave_policy_assignment(
			employee.name,
			leave_policy_1.name,
			year_start,
			year_end,
		).submit()

		new_assignment_date = add_months(year_start, 6)
		leave_application = frappe.get_doc(
			doctype="Leave Application",
			employee=employee.name,
			leave_type=leave_type.name,
			from_date=add_days(new_assignment_date, -1),
			to_date=add_days(new_assignment_date, 1),
			company="_Test Company",
			status="Approved",
			leave_approver="test@example.com",
		)
		leave_application.submit()
		new_leave_policy_assignment = create_leave_policy_assignment(
			employee.name,
			leave_policy_2.name,
			new_assignment_date,
			year_end,
		)
		new_leave_policy_assignment.mid_period_change = True
		# Application period cannot be across two allocation records
		self.assertRaises(LeaveAcrossAllocationsMidPeriodError, new_leave_policy_assignment.submit)

	def tearDown(self):
		frappe.db.set_value("Employee", self.employee.name, "date_of_joining", self.original_doj)


def create_leave_policy_assignment(employee, leave_policy, effective_from, effective_to):
	leave_policy_assignment = frappe.new_doc("Leave Policy Assignment")
	leave_policy_assignment.employee = employee
	leave_policy_assignment.leave_policy = leave_policy
	leave_policy_assignment.effective_from = effective_from
	leave_policy_assignment.effective_to = effective_to
	return leave_policy_assignment
