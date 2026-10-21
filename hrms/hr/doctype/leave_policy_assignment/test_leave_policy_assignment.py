# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, add_months, get_first_day, get_year_ending, get_year_start, getdate

from hrms.hr.doctype.leave_allocation.test_earned_leaves import get_allocated_leaves
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
	def setUp(self):
		employee = get_employee()
		self.original_doj = employee.date_of_joining
		self.employee = employee

	def test_grant_leaves(self):
		leave_period = get_leave_period(current=True)
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
		leave_period = get_leave_period(current=True)
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
		leave_period = get_leave_period(current=True)
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

		leave_period = create_leave_period(add_months(first_day, -23), first_day, "_Test Company")
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
		).save()

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
		frappe.flags.pop("current_date", None)

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
		leave_period = create_leave_period(year_start_date, year_end_date, "_Test Company")

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
		leave_period = create_leave_period(first_year_start_date, second_year_end_date, "_Test Company")

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
		leave_period = create_leave_period(get_year_start(today), get_year_ending(today), "_Test Company")

		sick = create_leave_type(
			leave_type_name="_Test Sick Leave", non_encashable_leaves=0, max_leaves_allowed=2
		)
		sick.allow_negative = 1
		sick.save()
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

		self.assertEqual(len(comments), 1)
		self.assertIn(casual.name, comments[0]["content"])

		allocations = frappe.get_all(
			"Leave Allocation",
			filters={"leave_policy_assignment": assignment.name},
			fields=["leave_type", "new_leaves_allocated", "total_leaves_allocated"],
		)
		allocations = {allocation["leave_type"]: allocation for allocation in allocations}

		self.assertEqual(allocations[sick.name]["new_leaves_allocated"], 0)
		self.assertEqual(allocations[sick.name]["total_leaves_allocated"], 0)
		self.assertEqual(allocations[compoff.name]["new_leaves_allocated"], 3)
		self.assertEqual(allocations[annual.name]["new_leaves_allocated"], 3)
		self.assertNotIn(casual.name, allocations)

	def test_half_yearly_earned_leave_schedule_based_on_leave_period(self):
		"""
		Leave Period: 01-Apr-2026 to 31-Mar-2027
		Expected allocation dates: 30-Sep-2026, 31-Mar-2027
		NOT: 30-Jun-2026, 31-Dec-2026
		"""
		leave_period = create_leave_period(getdate("2026-04-01"), getdate("2027-03-31"), "_Test Company")
		leave_type = create_leave_type(
			leave_type_name="_Test Half Yearly Earned Leave",
			is_earned_leave=True,
			earned_leave_frequency="Half-Yearly",
			allocate_on_day="Last Day",
		)
		annual_allocation = 18
		leave_policy = create_leave_policy(leave_type=leave_type.name, annual_allocation=annual_allocation)
		leave_policy.submit()

		# assignment created at the start of the leave period
		frappe.flags.current_date = getdate("2026-04-01")

		data = frappe._dict(
			{
				"assignment_based_on": "Leave Period",
				"leave_policy": leave_policy.name,
				"leave_period": leave_period.name,
			}
		)
		assignment = create_assignment(self.employee.name, data)
		assignment.submit()

		allocation_name = frappe.db.get_value(
			"Leave Allocation", {"leave_policy_assignment": assignment.name}, "name"
		)
		schedule = frappe.get_all(
			"Earned Leave Schedule",
			filters={"parent": allocation_name},
			fields=["allocation_date"],
			order_by="allocation_date asc",
		)

		allocation_dates = [getdate(row.allocation_date) for row in schedule]

		self.assertIn(getdate("2026-09-30"), allocation_dates)
		self.assertIn(getdate("2027-03-31"), allocation_dates)
		self.assertNotIn(getdate("2026-06-30"), allocation_dates)
		self.assertNotIn(getdate("2026-12-31"), allocation_dates)

		# should be exactly 2 allocations, not 3
		self.assertEqual(len(allocation_dates), 2)

	def test_half_yearly_earned_leave_schedule_based_on_joining_date(self):
		"""
		Employee joins: 01-Apr-2026
		Expected allocation dates: 30-Sep-2026, 31-Mar-2027
		"""
		self.employee.date_of_joining = getdate("2026-04-01")
		self.employee.save()

		leave_type = create_leave_type(
			leave_type_name="_Test Half Yearly Earned Leave Joining Date",
			is_earned_leave=True,
			earned_leave_frequency="Half-Yearly",
			allocate_on_day="Last Day",
		)
		annual_allocation = 18
		leave_policy = create_leave_policy(leave_type=leave_type.name, annual_allocation=annual_allocation)
		leave_policy.submit()

		frappe.flags.current_date = getdate("2026-04-01")

		data = frappe._dict(
			{
				"assignment_based_on": "Joining Date",
				"leave_policy": leave_policy.name,
				"effective_from": self.employee.date_of_joining,
				"effective_to": getdate("2027-03-31"),
			}
		)
		assignment = create_assignment(self.employee.name, data)
		assignment.submit()

		allocation_name = frappe.db.get_value(
			"Leave Allocation", {"leave_policy_assignment": assignment.name}, "name"
		)
		schedule = frappe.get_all(
			"Earned Leave Schedule",
			filters={"parent": allocation_name},
			fields=["allocation_date"],
			order_by="allocation_date asc",
		)

		allocation_dates = [getdate(row.allocation_date) for row in schedule]

		self.assertIn(getdate("2026-09-30"), allocation_dates)
		self.assertIn(getdate("2027-03-31"), allocation_dates)
		self.assertNotIn(getdate("2026-06-30"), allocation_dates)
		self.assertEqual(len(allocation_dates), 2)

	def test_half_yearly_earned_leave_schedule_based_on_joining_date_mid_month_first_day(self):
		"""
		Employee joins: 27-May-2026 (mid-month), assignment created: 03-Jul-2026
		Period 1: 27-May-2026 → 26-Nov-2026, Period 2: 27-Nov-2026 → 26-May-2027
		Expected allocation dates: 03-Jul-2026 (period 1 credited on assignment date), 27-Nov-2026
		"""
		self.employee.date_of_joining = getdate("2026-05-27")
		self.employee.save()

		leave_type = create_leave_type(
			leave_type_name="_Test Half Yearly Earned Leave Joining Date First Day",
			is_earned_leave=True,
			earned_leave_frequency="Half-Yearly",
			allocate_on_day="First Day",
		)
		annual_allocation = 18
		leave_policy = create_leave_policy(leave_type=leave_type.name, annual_allocation=annual_allocation)
		leave_policy.submit()

		# assignment created mid-period
		frappe.flags.current_date = getdate("2026-07-03")

		data = frappe._dict(
			{
				"assignment_based_on": "Joining Date",
				"leave_policy": leave_policy.name,
				"effective_from": self.employee.date_of_joining,
				"effective_to": getdate("2027-05-26"),
			}
		)
		assignment = create_assignment(self.employee.name, data)
		assignment.submit()

		allocation_name = frappe.db.get_value(
			"Leave Allocation", {"leave_policy_assignment": assignment.name}, "name"
		)
		schedule = frappe.get_all(
			"Earned Leave Schedule",
			filters={"parent": allocation_name},
			fields=["allocation_date"],
			order_by="allocation_date asc",
		)

		allocation_dates = [getdate(row.allocation_date) for row in schedule]

		self.assertIn(getdate("2026-07-03"), allocation_dates)
		self.assertIn(getdate("2026-11-27"), allocation_dates)
		self.assertNotIn(getdate("2026-06-30"), allocation_dates)
		self.assertNotIn(getdate("2027-05-27"), allocation_dates)

		# should be exactly 2 allocations, not 3
		self.assertEqual(len(allocation_dates), 2)

	def test_half_yearly_earned_leave_schedule_based_on_joining_date_mid_month_last_day(self):
		"""
		Employee joins: 27-May-2026 (mid-month), assignment created: 03-Jul-2026
		Period 1: 27-May-2026 → 26-Nov-2026, Period 2: 27-Nov-2026 → 26-May-2027
		Expected allocation dates: 26-Nov-2026, 26-May-2027
		"""
		self.employee.date_of_joining = getdate("2026-05-27")
		self.employee.save()

		leave_type = create_leave_type(
			leave_type_name="_Test Half Yearly Earned Leave Joining Date Last Day",
			is_earned_leave=True,
			earned_leave_frequency="Half-Yearly",
			allocate_on_day="Last Day",
		)
		annual_allocation = 18
		leave_policy = create_leave_policy(leave_type=leave_type.name, annual_allocation=annual_allocation)
		leave_policy.submit()

		# assignment created mid-period
		frappe.flags.current_date = getdate("2026-07-03")

		data = frappe._dict(
			{
				"assignment_based_on": "Joining Date",
				"leave_policy": leave_policy.name,
				"effective_from": self.employee.date_of_joining,
				"effective_to": getdate("2027-05-26"),
			}
		)
		assignment = create_assignment(self.employee.name, data)
		assignment.submit()

		allocation_name = frappe.db.get_value(
			"Leave Allocation", {"leave_policy_assignment": assignment.name}, "name"
		)
		schedule = frappe.get_all(
			"Earned Leave Schedule",
			filters={"parent": allocation_name},
			fields=["allocation_date"],
			order_by="allocation_date asc",
		)

		allocation_dates = [getdate(row.allocation_date) for row in schedule]

		self.assertIn(getdate("2026-11-26"), allocation_dates)
		self.assertIn(getdate("2027-05-26"), allocation_dates)
		self.assertNotIn(getdate("2026-06-30"), allocation_dates)

		# should be exactly 2 allocations, not 3
		self.assertEqual(len(allocation_dates), 2)

	def test_max_leaves_allowed_ignores_previous_allocation_in_overlapping_leave_period(self):
		"""
		Leave Periods: 2025 and 2026 (calendar year)
		Previous allocation: 01-Feb-2024 to 31-Jan-2025
		Current allocation: 01-Feb-2025 to 31-Jan-2026, overlaps both leave periods
		"""
		create_leave_period(getdate("2025-01-01"), getdate("2025-12-31"), "_Test Company")
		create_leave_period(getdate("2026-01-01"), getdate("2026-12-31"), "_Test Company")
		leave_type = create_leave_type(leave_type_name="_Test Max Leaves Type", max_leaves_allowed=12)
		leave_policy = create_leave_policy(leave_type=leave_type.name, annual_allocation=12)
		leave_policy.submit()

		self.employee.date_of_joining = getdate("2024-01-01")
		self.employee.save()

		previous_assignment = create_assignment(
			self.employee.name,
			frappe._dict(
				{
					"leave_policy": leave_policy.name,
					"effective_from": "2024-02-01",
					"effective_to": "2025-01-31",
				}
			),
		)
		previous_assignment.submit()

		current_assignment = create_assignment(
			self.employee.name,
			frappe._dict(
				{
					"leave_policy": leave_policy.name,
					"effective_from": "2025-02-01",
					"effective_to": "2026-01-31",
				}
			),
		)
		current_assignment.submit()

		self.assertEqual(get_allocated_leaves(current_assignment.name), 12)

	def test_allocation_linked_to_leave_period(self):
		leave_period = get_leave_period(current=True)
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

		self.assertEqual(
			frappe.db.get_value(
				"Leave Allocation", {"leave_policy_assignment": assignments[0]}, "leave_period"
			),
			leave_period.name,
		)

	def test_joining_date_assignment_runs_for_one_year(self):
		leave_policy = create_leave_policy(annual_allocation=12)
		leave_policy.submit()

		self.employee.date_of_joining = getdate("2025-03-10")
		self.employee.save()

		assignment = frappe.get_doc(
			{
				"doctype": "Leave Policy Assignment",
				"employee": self.employee.name,
				"assignment_based_on": "Joining Date",
				"leave_policy": leave_policy.name,
			}
		).insert()
		self.assertEqual(getdate(assignment.effective_to), getdate("2026-03-09"))

	def test_assignment_period_before_joining_date(self):
		leave_period = get_leave_period(current=True)
		leave_policy = create_leave_policy(annual_allocation=12)
		leave_policy.submit()

		self.employee.date_of_joining = add_days(leave_period.to_date, 30)
		self.employee.save()

		data = frappe._dict(
			{
				"assignment_based_on": "Leave Period",
				"leave_policy": leave_policy.name,
				"leave_period": leave_period.name,
			}
		)
		self.assertRaises(frappe.ValidationError, create_assignment, self.employee.name, data)

	def test_leave_period_validation(self):
		leave_policy = create_leave_policy(annual_allocation=12)
		leave_policy.submit()

		data = frappe._dict({"assignment_based_on": "Leave Period", "leave_policy": leave_policy.name})
		self.assertRaises(frappe.MandatoryError, create_assignment, self.employee.name, data)

		other_company_period = create_leave_period(
			getdate("2026-01-01"), getdate("2026-12-31"), "_Test Company 1"
		)
		data.leave_period = other_company_period.name
		self.assertRaises(frappe.ValidationError, create_assignment, self.employee.name, data)

	def _get_schedule_for_assignment_on(self, submission_date, allocate_on_day, date_of_joining):
		leave_type = create_leave_type(
			leave_type_name=f"_Test Earned Leave {allocate_on_day}",
			is_earned_leave=True,
			earned_leave_frequency="Monthly",
			allocate_on_day=allocate_on_day,
		)
		leave_type.db_set("rounding", "")
		leave_policy = create_leave_policy(leave_type=leave_type.name, annual_allocation=12)
		leave_policy.submit()

		self.employee.date_of_joining = getdate(date_of_joining)
		self.employee.save()

		frappe.flags.current_date = getdate(submission_date)
		assignment = create_assignment(
			self.employee.name,
			frappe._dict(
				{
					"leave_policy": leave_policy.name,
					"effective_from": "2026-01-01",
					"effective_to": "2026-12-31",
				}
			),
		)
		assignment.submit()
		frappe.flags.current_date = None

		allocation = frappe.get_doc("Leave Allocation", {"leave_policy_assignment": assignment.name})
		pending = [row for row in allocation.earned_leave_schedule if not row.is_allocated]
		return allocation, sorted(pending, key=lambda row: getdate(row.allocation_date))

	def test_earned_leave_schedule_submitted_on_last_day_of_period(self):
		allocation, pending = self._get_schedule_for_assignment_on("2026-06-30", "Last Day", "2024-01-01")

		self.assertEqual(allocation.new_leaves_allocated, 6)
		self.assertEqual(getdate(pending[0].allocation_date), getdate("2026-07-31"))
		self.assertEqual(getdate(pending[-1].allocation_date), getdate("2026-12-31"))
		self.assertEqual(sum(row.number_of_leaves for row in pending), 6)

	def test_earned_leave_schedule_submitted_before_date_of_joining_day(self):
		allocation, pending = self._get_schedule_for_assignment_on(
			"2026-06-10", "Date of Joining", "2024-01-20"
		)

		self.assertEqual(allocation.new_leaves_allocated, 5)
		self.assertEqual(getdate(pending[0].allocation_date), getdate("2026-06-20"))
		self.assertEqual(sum(row.number_of_leaves for row in pending), 7)

	def test_earned_leave_schedule_for_mid_period_joiner(self):
		leave_type = create_leave_type(
			leave_type_name="_Test Earned Leave Mid Period Joiner",
			is_earned_leave=True,
			earned_leave_frequency="Monthly",
			allocate_on_day="First Day",
		)
		leave_type.db_set("rounding", "")
		leave_policy = create_leave_policy(leave_type=leave_type.name, annual_allocation=12)
		leave_policy.submit()

		self.employee.date_of_joining = getdate("2026-06-15")
		self.employee.save()

		frappe.flags.current_date = getdate("2026-03-10")
		assignment = create_assignment(
			self.employee.name,
			frappe._dict(
				{
					"leave_policy": leave_policy.name,
					"effective_from": "2026-01-01",
					"effective_to": "2026-12-31",
				}
			),
		)
		assignment.submit()
		frappe.flags.current_date = None

		allocation = frappe.get_doc("Leave Allocation", {"leave_policy_assignment": assignment.name})
		schedule = sorted(allocation.earned_leave_schedule, key=lambda row: getdate(row.allocation_date))

		self.assertEqual(allocation.new_leaves_allocated, 0)
		self.assertEqual(getdate(schedule[0].allocation_date), getdate("2026-06-15"))
		self.assertAlmostEqual(schedule[0].number_of_leaves, 16 / 30, places=2)
		self.assertEqual(len(schedule), 7)
		self.assertFalse(any(row.is_allocated for row in schedule))
		self.assertAlmostEqual(sum(row.number_of_leaves for row in schedule), 6 + 16 / 30, places=2)
