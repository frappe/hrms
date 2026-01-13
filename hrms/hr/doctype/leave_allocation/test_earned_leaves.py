import frappe
from frappe.utils import (
	add_days,
	add_months,
	add_to_date,
	get_first_day,
	get_last_day,
	get_year_ending,
	get_year_start,
	getdate,
)
from frappe.utils.user import add_role

from hrms.hr.doctype.holiday_list_assignment.test_holiday_list_assignment import assign_holiday_list
from hrms.hr.doctype.leave_allocation.test_leave_allocation import create_leave_allocation
from hrms.hr.doctype.leave_application.leave_application import (
	get_leave_balance_on,
	get_leave_details,
)
from hrms.hr.doctype.leave_application.test_leave_application import make_leave_application
from hrms.hr.doctype.leave_policy_assignment.leave_policy_assignment import (
	calculate_pro_rated_leaves,
	create_assignment_for_multiple_employees,
)
from hrms.hr.utils import allocate_earned_leaves, round_earned_leaves
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_holiday_list
from hrms.tests.test_utils import get_first_sunday
from hrms.tests.utils import HRMSTestSuite


class TestLeaveAllocation(HRMSTestSuite):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.make_employees()
		cls.make_leave_types()

	def setUp(self):
		for doctype in [
			"Leave Period",
			"Leave Application",
			"Leave Allocation",
			"Leave Policy Assignment",
			"Leave Ledger Entry",
		]:
			frappe.db.delete(doctype)

		employee = frappe.get_doc("Employee", "_T-Employee-00001")
		self.original_doj = employee.date_of_joining
		employee.date_of_joining = add_months(getdate(), -24)
		employee.save()

		employee2 = frappe.get_doc("Employee", "_T-Employee-00002")
		employee2.date_of_joining = add_months(getdate(), -24)
		employee2.save()

		self.employee = employee
		self.leave_type = "Test Earned Leave"

		from_date = get_year_start(getdate())
		to_date = get_year_ending(getdate())
		self.holiday_list = make_holiday_list(from_date=from_date, to_date=to_date)
		frappe.db.set_value("Email Account", "_Test Email Account 1", "default_outgoing", 1)

	def test_earned_leave_allocation(self):
		"""Tests if Earned Leave allocation is 0 initially as it happens via scheduler"""
		# second last day of the month
		# leaves allocated should be 0 since it is an earned leave and allocation happens via scheduler based on set frequency
		frappe.flags.current_date = add_days(get_last_day(getdate()), -1)
		leave_policy_assignments = make_policy_assignment(self.employee)

		leaves_allocated = get_allocated_leaves(leave_policy_assignments[0])
		self.assertEqual(leaves_allocated, 0)

	def test_earned_leave_update_after_submission(self):
		"""Tests if validation error is raised when updating Earned Leave allocation after submission"""
		leave_policy_assignments = make_policy_assignment(self.employee)

		allocation = frappe.db.get_value(
			"Leave Allocation",
			{"leave_policy_assignment": leave_policy_assignments[0]},
			"name",
		)
		allocation = frappe.get_doc("Leave Allocation", allocation)
		allocation.new_leaves_allocated = 2
		self.assertRaises(frappe.ValidationError, allocation.save)

	def test_alloc_based_on_leave_period(self):
		"""Case 1: Tests if assignment created one month after the leave period
		allocates 1 leave for past month"""
		start_date = get_first_day(add_months(getdate(), -1))

		frappe.flags.current_date = get_first_day(getdate())
		leave_policy_assignments = make_policy_assignment(self.employee, start_date=start_date)

		leaves_allocated = get_allocated_leaves(leave_policy_assignments[0])
		self.assertEqual(leaves_allocated, 1)

	def test_alloc_on_month_end_based_on_leave_period(self):
		"""Case 2: Tests if assignment created on the last day of the leave period's latter month
		allocates 1 leave for the current month even though the month has not ended
		since the daily job might have already executed (12:00:00 AM)"""
		start_date = get_first_day(add_months(getdate(), -2))

		frappe.flags.current_date = get_last_day(getdate())
		leave_policy_assignments = make_policy_assignment(self.employee, start_date=start_date)

		leaves_allocated = get_allocated_leaves(leave_policy_assignments[0])
		self.assertEqual(leaves_allocated, 3)

	def test_alloc_based_on_leave_period_with_cf_leaves(self):
		"""Case 3: Tests assignment created on the leave period's latter month with carry forwarding"""
		start_date = get_first_day(add_months(getdate(), -2))

		# initial leave allocation = 5
		leave_allocation = create_leave_allocation(
			employee=self.employee.name,
			employee_name=self.employee.employee_name,
			leave_type="Test Earned Leave",
			from_date=add_months(getdate(), -12),
			to_date=add_months(getdate(), -3),
			new_leaves_allocated=5,
			carry_forward=0,
		)
		leave_allocation.submit()

		frappe.flags.current_date = get_last_day(add_months(getdate(), -1))
		# carry forwarded leaves = 5, 2 leaves allocated for passed months
		leave_policy_assignments = make_policy_assignment(
			self.employee, start_date=start_date, carry_forward=1
		)

		details = frappe.db.get_value(
			"Leave Allocation",
			{"leave_policy_assignment": leave_policy_assignments[0]},
			["total_leaves_allocated", "new_leaves_allocated", "unused_leaves", "name"],
			as_dict=True,
		)
		self.assertEqual(details.new_leaves_allocated, 2)
		self.assertEqual(details.unused_leaves, 5)
		self.assertEqual(details.total_leaves_allocated, 7)

	def test_alloc_based_on_joining_date(self):
		"""Tests if DOJ-based assignment created 2 months after the DOJ
		allocates 3 leaves for the past 2 months"""
		self.employee.date_of_joining = get_first_day(add_months(getdate(), -2))
		self.employee.save()

		# assignment created on the last day of the current month
		frappe.flags.current_date = get_last_day(getdate())
		"""set end date while making assignment based on Joining date because while start date is fetched from
		employee master, make_policy_assignment ends up taking current date as end date if not specified which
		causes the date of assignment to be later than the end date of leave period"""
		start_date = self.employee.date_of_joining
		end_date = get_last_day(add_months(self.employee.date_of_joining, 12))
		leave_policy_assignments = make_policy_assignment(
			self.employee, assignment_based_on="Joining Date", start_date=start_date, end_date=end_date
		)
		leaves_allocated = get_allocated_leaves(leave_policy_assignments[0])
		effective_from = frappe.db.get_value(
			"Leave Policy Assignment", leave_policy_assignments[0], "effective_from"
		)
		self.assertEqual(effective_from, self.employee.date_of_joining)
		self.assertEqual(leaves_allocated, 3)

	def test_alloc_on_doj_based_on_leave_period(self):
		"""Tests assignment with 'Allocate On=Date of Joining' based on Leave Period"""
		start_date = get_first_day(add_months(getdate(), -2))

		# joining date set to 2 months back
		self.employee.date_of_joining = start_date
		self.employee.save()

		# assignment created on the same day of the current month, should allocate leaves including the current month
		frappe.flags.current_date = get_first_day(getdate())

		leave_policy_assignments = make_policy_assignment(
			self.employee, start_date=start_date, allocate_on_day="Date of Joining"
		)
		leaves_allocated = get_allocated_leaves(leave_policy_assignments[0])
		self.assertEqual(leaves_allocated, 3)

	def test_alloc_on_doj_based_on_joining_date(self):
		"""Tests assignment with 'Allocate On=Date of Joining' based on Joining Date"""
		# joining date set to 2 months back
		# leave should be allocated for current month too since this day is same as the joining day
		self.employee.date_of_joining = get_first_day(add_months(getdate(), -2))
		self.employee.save()

		# assignment created on the first day of the current month
		frappe.flags.current_date = get_first_day(getdate())

		leave_policy_assignments = make_policy_assignment(
			self.employee,
			allocate_on_day="Date of Joining",
			assignment_based_on="Joining Date",
			end_date=get_last_day(add_months(self.employee.date_of_joining, 12)),
		)
		leaves_allocated = get_allocated_leaves(leave_policy_assignments[0])
		effective_from = frappe.db.get_value(
			"Leave Policy Assignment", leave_policy_assignments[0], "effective_from"
		)
		self.assertEqual(effective_from, self.employee.date_of_joining)
		self.assertEqual(leaves_allocated, 3)

	def test_earned_leaves_creation(self):
		frappe.flags.current_date = get_year_start(getdate())
		make_policy_assignment(
			self.employee,
			annual_allocation=6,
			allocate_on_day="First Day",
			start_date=frappe.flags.current_date,
		)

		# leaves for 6 months = 3, but max leaves restricts allocation to 2
		frappe.db.set_value("Leave Type", self.leave_type, "max_leaves_allowed", 2)
		allocate_earned_leaves_for_months(6)
		self.assertEqual(
			get_leave_balance_on(self.employee.name, self.leave_type, frappe.flags.current_date), 2
		)

		# validate earned leaves creation without maximum leaves
		frappe.db.set_value("Leave Type", self.leave_type, "max_leaves_allowed", 0)
		allocate_earned_leaves_for_months(6)
		self.assertEqual(
			get_leave_balance_on(self.employee.name, self.leave_type, frappe.flags.current_date), 5
		)

	def test_overallocation(self):
		"""Tests earned leave allocation does not exceed annual allocation"""
		frappe.flags.current_date = get_year_start(getdate())
		make_policy_assignment(
			self.employee,
			annual_allocation=22,
			allocate_on_day="First Day",
			start_date=frappe.flags.current_date,
		)

		# leaves for 12 months = 22
		# With rounding, 22 leaves would be allocated in 11 months only
		frappe.db.set_value("Leave Type", self.leave_type, "rounding", 1.0)
		allocate_earned_leaves_for_months(11)
		self.assertEqual(
			get_leave_balance_on(self.employee.name, self.leave_type, frappe.flags.current_date), 22
		)

		# should not allocate more leaves than annual allocation
		allocate_earned_leaves_for_months(1)
		self.assertEqual(
			get_leave_balance_on(self.employee.name, self.leave_type, frappe.flags.current_date), 22
		)

	def test_over_allocation_during_assignment_creation(self):
		"""Tests backdated earned leave allocation does not exceed annual allocation"""
		start_date = get_first_day(add_months(getdate(), -12))

		# joining date set to 1Y ago
		self.employee.date_of_joining = start_date
		self.employee.save()

		# create backdated assignment for last year
		frappe.flags.current_date = get_first_day(getdate())

		leave_policy_assignments = make_policy_assignment(
			self.employee, start_date=start_date, allocate_on_day="Date of Joining"
		)

		# 13 months have passed but annual allocation = 12
		# check annual allocation is not exceeded
		leaves_allocated = get_allocated_leaves(leave_policy_assignments[0])
		self.assertEqual(leaves_allocated, 12)

	def test_overallocation_with_carry_forwarding(self):
		"""Tests earned leave allocation with cf leaves does not exceed annual allocation"""
		year_start = get_year_start(getdate())

		# initial leave allocation = 5
		leave_allocation = create_leave_allocation(
			employee=self.employee.name,
			employee_name=self.employee.employee_name,
			leave_type=self.leave_type,
			from_date=get_first_day(add_months(year_start, -1)),
			to_date=get_last_day(add_months(year_start, -1)),
			new_leaves_allocated=5,
			carry_forward=0,
		)
		leave_allocation.submit()

		frappe.flags.current_date = year_start
		# carry forwarded leaves = 5
		make_policy_assignment(
			self.employee,
			annual_allocation=22,
			allocate_on_day="First Day",
			start_date=year_start,
			carry_forward=True,
		)

		frappe.db.set_value("Leave Type", self.leave_type, "rounding", 1.0)
		allocate_earned_leaves_for_months(11)

		# 5 carry forwarded leaves + 22 EL allocated = 27 leaves
		self.assertEqual(
			get_leave_balance_on(self.employee.name, self.leave_type, frappe.flags.current_date), 27
		)

		# should not allocate more leaves than annual allocation (22 excluding 5 cf leaves)
		allocate_earned_leaves_for_months(1)
		self.assertEqual(
			get_leave_balance_on(self.employee.name, self.leave_type, frappe.flags.current_date), 27
		)

	def test_allocate_on_first_day(self):
		"""Tests assignment with 'Allocate On=First Day'"""
		start_date = get_first_day(add_months(getdate(), -1))
		prev_month_last_day = get_last_day(add_months(getdate(), -1))
		first_day = get_first_day(getdate())

		# Case 1: Allocates 1 leave for the previous month if created on the previous month's last day
		frappe.flags.current_date = prev_month_last_day
		leave_policy_assignments = make_policy_assignment(
			self.employee, allocate_on_day="First Day", start_date=start_date
		)
		leaves_allocated = get_allocated_leaves(leave_policy_assignments[0])
		self.assertEqual(leaves_allocated, 1)

		# Case 2: Allocates 1 leave on the current month's first day (via scheduler)
		frappe.flags.current_date = first_day
		allocate_earned_leaves()
		leaves_allocated = get_allocated_leaves(leave_policy_assignments[0])
		self.assertEqual(leaves_allocated, 2)

	def test_allocate_on_last_day(self):
		"""Tests assignment with 'Allocate On=Last Day'"""
		prev_month_last_day = get_last_day(add_months(getdate(), -1))
		last_day = get_last_day(getdate())

		# Case 1: Allocates 1 leave for the previous month if created on the previous month's last day
		frappe.flags.current_date = prev_month_last_day
		leave_policy_assignments = make_policy_assignment(
			self.employee, allocate_on_day="Last Day", start_date=prev_month_last_day
		)
		leaves_allocated = get_allocated_leaves(leave_policy_assignments[0])
		self.assertEqual(leaves_allocated, 1)

		# Case 2: Allocates 1 leave on the current month's last day (via scheduler)
		frappe.flags.current_date = last_day
		allocate_earned_leaves()
		leaves_allocated = get_allocated_leaves(leave_policy_assignments[0])
		self.assertEqual(leaves_allocated, 2)

		# Case 3: Doesn't allocate before the current month's last day (via scheduler)
		frappe.flags.current_date = add_days(last_day, -1)
		allocate_earned_leaves()
		leaves_allocated = get_allocated_leaves(leave_policy_assignments[0])
		# balance is still 2
		self.assertEqual(leaves_allocated, 2)

	def test_allocate_on_date_of_joining(self):
		"""Tests assignment with 'Allocate On=Date of Joining'"""
		start_date = get_first_day(add_months(getdate(), -1))
		end_date = get_last_day(start_date)
		doj = add_days(start_date, 5)
		current_month_doj = add_days(get_first_day(getdate()), 5)

		self.employee.date_of_joining = doj
		self.employee.save()

		# Case 1: Allocates pro-rated leave for the previous month if created on the previous month's day of joining
		frappe.flags.current_date = doj
		leave_policy_assignments = make_policy_assignment(
			self.employee, allocate_on_day="Date of Joining", start_date=start_date
		)
		leaves_allocated = get_allocated_leaves(leave_policy_assignments[0])
		pro_rated_leave = round_earned_leaves(calculate_pro_rated_leaves(1, doj, start_date, end_date), "0.5")
		self.assertEqual(leaves_allocated, pro_rated_leave)

		# Case 2: Doesn't allocate before the current month's doj (via scheduler)
		frappe.flags.current_date = add_days(current_month_doj, -1)
		allocate_earned_leaves()
		leaves_allocated = get_allocated_leaves(leave_policy_assignments[0])
		# balance is still the same
		self.assertEqual(leaves_allocated, pro_rated_leave)

		# Case 3: Allocates 1 leave on the current month's day of joining (via scheduler)
		frappe.flags.current_date = current_month_doj
		allocate_earned_leaves()
		leaves_allocated = get_allocated_leaves(leave_policy_assignments[0])
		self.assertEqual(leaves_allocated, pro_rated_leave + 1)

	def test_backdated_pro_rated_allocation(self):
		# leave period started in Jan
		start_date = getdate("2023-01-01")

		# employee joined mid-month in Mar
		self.employee.date_of_joining = getdate("2023-03-15")
		self.employee.save()

		# creating backdated allocation in May
		frappe.flags.current_date = getdate("2023-05-16")
		leave_policy_assignments = make_policy_assignment(
			self.employee,
			allocate_on_day="First Day",
			start_date=start_date,
			rounding="",
		)
		leaves_allocated = get_allocated_leaves(leave_policy_assignments[0])

		# pro-rated leaves should be considered only for the month of DOJ i.e. Mar = 0.548 leaves
		# and full leaves for the remaining 2 months i.e. Apr and May = 2 leaves
		self.assertEqual(leaves_allocated, 2.548)

	def test_no_pro_rated_leaves_allocated_before_effective_date(self):
		start_date = get_first_day(add_months(getdate(), -1))
		doj = add_days(start_date, 5)

		self.employee.date_of_joining = doj
		self.employee.save()

		# assigning before DOJ
		frappe.flags.current_date = add_days(doj, -1)
		leave_policy_assignments = make_policy_assignment(
			self.employee, allocate_on_day="Date of Joining", start_date=start_date
		)
		leaves_allocated = get_allocated_leaves(leave_policy_assignments[0])
		self.assertEqual(leaves_allocated, 0.0)

	def test_pro_rated_allocation_via_scheduler(self):
		start_date = get_first_day(add_months(getdate(), -1))
		doj = add_days(start_date, 5)

		self.employee.date_of_joining = doj
		self.employee.save()

		# assigning before DOJ, no leaves allocated initially
		frappe.flags.current_date = add_days(doj, -1)
		leave_policy_assignments = make_policy_assignment(
			self.employee, allocate_on_day="First Day", start_date=start_date
		)

		# pro-rated leaves allocated during the first month
		frappe.flags.current_date = add_days(doj, -1)
		allocate_earned_leaves()
		leaves_allocated = get_allocated_leaves(leave_policy_assignments[0])
		pro_rated_leave = round_earned_leaves(
			calculate_pro_rated_leaves(1, doj, start_date, get_last_day(start_date)), "0.5"
		)
		self.assertEqual(leaves_allocated, pro_rated_leave)

	@assign_holiday_list("Salary Slip Test Holiday List", "_Test Company")
	def test_get_earned_leave_details_for_dashboard(self):
		frappe.flags.current_date = get_year_start(getdate())
		first_sunday = get_first_sunday(self.holiday_list, for_date=frappe.flags.current_date)

		leave_policy_assignments = make_policy_assignment(
			self.employee,
			annual_allocation=6,
			allocate_on_day="First Day",
			start_date=add_months(frappe.flags.current_date, -3),
		)
		allocation = frappe.db.get_value(
			"Leave Allocation",
			{"leave_policy_assignment": leave_policy_assignments[0]},
			"name",
		)
		# 2 leaves allocated for past months
		allocation = frappe.get_doc("Leave Allocation", allocation)

		allocate_earned_leaves_for_months(6)

		leave_date = add_days(first_sunday, 1)
		make_leave_application(self.employee.name, leave_date, leave_date, self.leave_type)

		# 2 leaves were allocated when the allocation was created
		details = get_leave_details(self.employee.name, allocation.from_date)
		leave_allocation = details["leave_allocation"][self.leave_type]
		expected = {
			"total_leaves": 2.0,
			"expired_leaves": 0.0,
			"leaves_taken": 1.0,
			"leaves_pending_approval": 0.0,
			"remaining_leaves": 1.0,
		}
		self.assertEqual(leave_allocation, expected)

		# total leaves allocated = 5 on the current date
		details = get_leave_details(self.employee.name, frappe.flags.current_date)
		leave_allocation = details["leave_allocation"][self.leave_type]
		expected = {
			"total_leaves": 5.0,
			"expired_leaves": 0.0,
			"leaves_taken": 1.0,
			"leaves_pending_approval": 0.0,
			"remaining_leaves": 4.0,
		}
		self.assertEqual(leave_allocation, expected)

	def test_allocate_leaves_manually(self):
		frappe.flags.current_date = get_year_start(getdate())
		lpas = make_policy_assignment(
			self.employee,
			allocate_on_day="First Day",
			start_date=frappe.flags.current_date,
		)

		leave_allocation = frappe.get_last_doc(
			"Leave Allocation", filters={"leave_policy_assignment": lpas[0]}
		)
		leave_allocation.allocate_leaves_manually(1)
		leave_allocation.allocate_leaves_manually(1)
		leave_allocation.allocate_leaves_manually(1)
		leave_allocation.allocate_leaves_manually(1)
		leave_allocation.allocate_leaves_manually(1)
		self.assertEqual(
			get_leave_balance_on(self.employee.name, self.leave_type, frappe.flags.current_date), 6
		)

		leave_allocation.allocate_leaves_manually(5)
		self.assertEqual(
			get_leave_balance_on(self.employee.name, self.leave_type, frappe.flags.current_date), 11
		)

		# manually set from_date - applicable from the next day
		leave_allocation.allocate_leaves_manually(1, add_days(frappe.flags.current_date, 1))
		# balance should be 11 on the current date
		self.assertEqual(
			get_leave_balance_on(self.employee.name, self.leave_type, frappe.flags.current_date), 11
		)
		# allocated leave should be applicable from the next day
		self.assertEqual(
			get_leave_balance_on(self.employee.name, self.leave_type, add_days(frappe.flags.current_date, 1)),
			12,
		)

		self.assertRaises(frappe.ValidationError, leave_allocation.allocate_leaves_manually, 1)

	def test_quarterly_earned_leaves_allocated_on_last_day_in_the_middle_of_leave_period(self):
		employee = frappe.get_doc("Employee", "_T-Employee-00002")
		# allocated after one quarter
		frappe.flags.current_date = add_months(get_year_start(getdate()), 4)

		assignment = make_policy_assignment(
			employee,
			allocate_on_day="Last Day",
			earned_leave_frequency="Quarterly",
			annual_allocation=12,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
		)[0]

		# quarter passed 1 so leaves allocated should be 3
		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)

		self.assertEqual(total_leaves_allocated, 3.0)

	def test_quarterly_earned_leaves_allocated_on_last_day_at_the_start_of_the_leave_period(self):
		frappe.flags.current_date = get_year_start(getdate())

		employee = frappe.get_doc("Employee", "_T-Employee-00002")

		assignment = make_policy_assignment(
			employee,
			allocate_on_day="Last Day",
			earned_leave_frequency="Quarterly",
			annual_allocation=12,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
		)[0]

		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)

		self.assertEqual(total_leaves_allocated, 0.0)

	def test_quartertly_earned_leaves_allocated_on_first_day_at_the_start_of_leave_period(self):
		frappe.flags.current_date = get_year_start(getdate())

		employee = frappe.get_doc("Employee", "_T-Employee-00002")

		assignment = make_policy_assignment(
			employee,
			allocate_on_day="First Day",
			earned_leave_frequency="Quarterly",
			annual_allocation=12,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
		)[0]

		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)

		self.assertEqual(total_leaves_allocated, 3.0)

	def test_quarterly_earned_leaves_allocated_by_the_scheduler(self):
		frappe.flags.current_date = get_year_start(getdate())

		employee = frappe.get_doc("Employee", "_T-Employee-00002")

		# created policy assignment at the begining of the year so allocated leaces should be 0
		assignment = make_policy_assignment(
			employee,
			allocate_on_day="First Day",
			earned_leave_frequency="Quarterly",
			annual_allocation=12,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
		)[0]

		# quarter passed 2 so leaves allocated should be 6
		frappe.flags.current_date = add_months(get_year_start(getdate()), 3)

		allocate_earned_leaves()

		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)
		self.assertEqual(total_leaves_allocated, 6)

		# quarter three passed so leaves allocated should be 9
		frappe.flags.current_date = add_months(get_year_start(getdate()), 9)
		allocate_earned_leaves()

		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)
		self.assertEqual(total_leaves_allocated, 9)

	def test_quarterly_leaves_allocated_pro_rated(self):
		# joined 1 month 10 days after the leave period date
		employee = frappe.get_doc("Employee", "_T-Employee-00002")
		employee.date_of_joining = add_to_date(get_year_start(getdate()), months=1, days=10)
		employee.save()

		# make policy assignment on the same day
		frappe.flags.current_date = add_to_date(get_year_start(getdate()), months=1, days=10)
		assignment = make_policy_assignment(
			employee,
			allocate_on_day="Last Day",
			earned_leave_frequency="Quarterly",
			annual_allocation=12,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
			rounding=0.25,
		)[0]

		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)
		# no allocation at the beginning
		self.assertEqual(total_leaves_allocated, 0)

		frappe.flags.current_date = add_to_date(get_year_start(getdate()), months=3, days=-1)
		allocate_earned_leaves()

		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)
		# 1 full for full month + 1/(28 days of feb)*20 days = 0.7142 rounded to 0.25 = 1.75
		self.assertEqual(total_leaves_allocated, 1.75)

	def test_half_yearly_earned_leaves_allocated_on_last_day_at_the_start_of_leave_period(self):
		frappe.flags.current_date = get_year_start(getdate())
		employee = frappe.get_doc("Employee", "_T-Employee-00002")

		assignment = make_policy_assignment(
			employee,
			allocate_on_day="Last Day",
			earned_leave_frequency="Half-Yearly",
			annual_allocation=12,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
		)[0]

		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)

		self.assertEqual(total_leaves_allocated, 0.0)

	def test_half_yearly_earned_leaves_allocated_on_last_day_in_the_middle_of_leave_period(self):
		employee = frappe.get_doc("Employee", "_T-Employee-00002")

		frappe.flags.current_date = add_months(get_year_start(getdate()), 7)

		assignment = make_policy_assignment(
			employee,
			allocate_on_day="Last Day",
			earned_leave_frequency="Half-Yearly",
			annual_allocation=12,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
		)[0]

		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)

		self.assertEqual(total_leaves_allocated, 6.0)

	def test_half_yearly_earned_leaves_allocated_on_first_day_at_the_start_of_leave_period(self):
		employee = frappe.get_doc("Employee", "_T-Employee-00002")

		frappe.flags.current_date = get_year_start(getdate())

		assignment = make_policy_assignment(
			employee,
			allocate_on_day="First Day",
			earned_leave_frequency="Half-Yearly",
			annual_allocation=12,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
		)[0]

		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)

		self.assertEqual(total_leaves_allocated, 6.0)

	def test_half_yearly_earned_leaves_allocated_by_the_scheduler(self):
		frappe.flags.current_date = get_year_start(getdate())

		employee = frappe.get_doc("Employee", "_T-Employee-00002")

		assignment = make_policy_assignment(
			employee,
			allocate_on_day="First Day",
			earned_leave_frequency="Half-Yearly",
			annual_allocation=12,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
		)[0]

		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)
		self.assertEqual(total_leaves_allocated, 6)

		# after 6 months, all 12 leaves should be allocated
		frappe.flags.current_date = add_months(get_year_start(getdate()), 6)

		allocate_earned_leaves()

		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)
		self.assertEqual(total_leaves_allocated, 12)

	def test_half_yearly_leaves_allocated_pro_rated(self):
		employee = frappe.get_doc("Employee", "_T-Employee-00002")
		employee.date_of_joining = add_to_date(get_year_start(getdate()), months=3, days=25)
		employee.save()

		# make policy assignment on the same day
		frappe.flags.current_date = add_to_date(get_year_start(getdate()), months=3, days=25)
		assignment = make_policy_assignment(
			employee,
			allocate_on_day="Last Day",
			earned_leave_frequency="Half-Yearly",
			annual_allocation=12,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
			rounding=0.25,
		)[0]

		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)

		self.assertEqual(total_leaves_allocated, 0)

		frappe.flags.current_date = add_to_date(get_year_start(getdate()), months=6, days=-1)
		allocate_earned_leaves()

		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)
		# 2 full + 1/30*5 = 2.166 rounded to 0.25
		self.assertEqual(total_leaves_allocated, 2.25)

	def test_yearly_leaves_allocated_on_last_day_at_the_start_of_the_period(self):
		employee = frappe.get_doc("Employee", "_T-Employee-00002")

		frappe.flags.current_date = get_year_start(getdate())
		# 4 year leave policy
		assignment = make_policy_assignment(
			employee,
			allocate_on_day="Last Day",
			earned_leave_frequency="Yearly",
			annual_allocation=12,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=add_to_date(get_year_ending(getdate()), years=4),
		)[0]

		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)

		self.assertEqual(total_leaves_allocated, 0.0)

	def test_yearly_leaves_allocated_on_last_day_in_the_middle_of_the_period(self):
		employee = frappe.get_doc("Employee", "_T-Employee-00002")

		frappe.flags.current_date = add_to_date(get_year_start(getdate()), years=2)
		# 4 year leave policy
		assignment = make_policy_assignment(
			employee,
			allocate_on_day="Last Day",
			earned_leave_frequency="Yearly",
			annual_allocation=12,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=add_to_date(get_year_ending(getdate()), years=4),
		)[0]

		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)

		self.assertEqual(total_leaves_allocated, 24.0)

	def test_yearly_leaves_allocated_on_first_day_at_the_start_of_the_period(self):
		employee = frappe.get_doc("Employee", "_T-Employee-00002")

		frappe.flags.current_date = get_year_start(getdate())
		# 4 year leave policy
		assignment = make_policy_assignment(
			employee,
			allocate_on_day="First Day",
			earned_leave_frequency="Yearly",
			annual_allocation=12,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=add_to_date(get_year_ending(getdate()), years=4),
		)[0]

		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)

		self.assertEqual(total_leaves_allocated, 12.0)

	def test_yearly_leaves_allocated_by_scheduler(self):
		frappe.flags.current_date = get_year_start(getdate())

		employee = frappe.get_doc("Employee", "_T-Employee-00002")

		assignment = make_policy_assignment(
			employee,
			allocate_on_day="First Day",
			earned_leave_frequency="Yearly",
			annual_allocation=12,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=add_to_date(get_year_ending(getdate()), years=4),
		)[0]

		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)
		self.assertEqual(total_leaves_allocated, 12)

		frappe.flags.current_date = add_months(get_year_start(getdate()), 12)

		allocate_earned_leaves()

		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)
		self.assertEqual(total_leaves_allocated, 24)

	def test_yearly_leaves_allocated_pro_rated(self):
		employee = frappe.get_doc("Employee", "_T-Employee-00002")
		employee.date_of_joining = add_to_date(get_year_start(getdate()), months=7, days=15)
		employee.save()

		# make policy assignment on the same day
		frappe.flags.current_date = add_to_date(get_year_start(getdate()), months=7, days=15)
		assignment = make_policy_assignment(
			employee,
			allocate_on_day="Last Day",
			earned_leave_frequency="Yearly",
			annual_allocation=12,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=add_to_date(get_year_ending(getdate()), years=4),
			rounding=0.25,
		)[0]

		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)

		self.assertEqual(total_leaves_allocated, 0)

		frappe.flags.current_date = get_year_ending(getdate())
		allocate_earned_leaves()

		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)
		# 4 months full leave 1/30*15 = 0.5 rounded to 0.25
		self.assertEqual(total_leaves_allocated, 4.5)

	def test_error_logging_failed_allocations(self):
		frappe.flags.current_date = get_year_start(getdate())
		assignment = make_policy_assignment(
			self.employee,
			allocate_on_day="First Day",
			earned_leave_frequency="Monthly",
			annual_allocation=24,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
			rounding=0.25,
		)[0]
		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": self.employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)
		self.assertEqual(total_leaves_allocated, 2)
		frappe.db.set_value("Leave Type", self.leave_type, "max_leaves_allowed", 2)
		frappe.flags.current_date = add_months(get_year_start(getdate()), 1)
		allocate_earned_leaves()
		error_log = frappe.db.get_value("Error Log", {"reference_doctype": "Leave Allocation"})
		self.assertIsNotNone(error_log)

	def test_send_email_for_failed_allocations(self):
		frappe.flags.current_date = get_year_start(getdate())
		assignment = make_policy_assignment(
			self.employee,
			allocate_on_day="First Day",
			earned_leave_frequency="Monthly",
			annual_allocation=24,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
			rounding=0.25,
		)[0]
		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": self.employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)
		self.assertEqual(total_leaves_allocated, 2)
		frappe.db.set_value("Leave Type", self.leave_type, "max_leaves_allowed", 2)
		frappe.flags.current_date = add_months(get_year_start(getdate()), 1)
		allocate_earned_leaves()
		email = frappe.db.get_values(
			"Email Queue", {"message": ("like Failure of Automatic Allocation of Earned Leaves%")}
		)
		self.assertIsNotNone(email)

	def test_retry_failed_allocations(self):
		frappe.flags.current_date = get_year_start(getdate())
		assignment = make_policy_assignment(
			self.employee,
			allocate_on_day="First Day",
			earned_leave_frequency="Monthly",
			annual_allocation=24,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
			rounding=0.25,
		)[0]
		leave_allocation = frappe.get_doc(
			"Leave Allocation", {"employee": self.employee.name, "leave_policy_assignment": assignment}
		)
		frappe.db.set_value("Leave Type", self.leave_type, "max_leaves_allowed", 2)
		# second month failed
		frappe.flags.current_date = add_months(get_year_start(getdate()), 1)
		allocate_earned_leaves()
		# third month failed
		frappe.flags.current_date = add_months(get_year_start(getdate()), 2)
		allocate_earned_leaves()
		# total failed should be 2
		failed_allocations = frappe.get_all(
			"Earned Leave Schedule", {"parent": leave_allocation.name, "attempted": 1, "failed": 1}, ["*"]
		)
		self.assertEqual(len(failed_allocations), 2)
		frappe.db.set_value("Leave Type", self.leave_type, "max_leaves_allowed", 0)
		leave_allocation.retry_failed_allocations(failed_allocations)
		failed_allocations = frappe.get_all(
			"Earned Leave Schedule", {"parent": leave_allocation.name, "attempted": 1, "failed": 1}
		)
		self.assertFalse(failed_allocations)

		total_leaves_allocated = frappe.get_value(
			"Leave Allocation",
			{"employee": self.employee.name, "leave_policy_assignment": assignment},
			"total_leaves_allocated",
		)
		self.assertEqual(total_leaves_allocated, 6)

	def test_permission_check_for_retrying_failed_allocation(self):
		frappe.flags.current_date = get_year_start(getdate())
		assignment = make_policy_assignment(
			self.employee,
			allocate_on_day="First Day",
			earned_leave_frequency="Monthly",
			annual_allocation=24,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
			rounding=0.25,
		)[0]
		leave_allocation = frappe.get_doc(
			"Leave Allocation", {"employee": self.employee.name, "leave_policy_assignment": assignment}
		)
		failed_allocations = frappe.get_all(
			"Earned Leave Schedule", {"parent": leave_allocation.name, "attempted": 1, "failed": 1}, ["*"]
		)
		frappe.set_user(self.employee.user_id)
		self.assertRaises(
			frappe.PermissionError, leave_allocation.retry_failed_allocations, failed_allocations
		)
		add_role(self.employee.user_id, "HR Manager")
		leave_allocation.retry_failed_allocations(failed_allocations)
		failed_allocations = frappe.get_all(
			"Earned Leave Schedule", {"parent": leave_allocation.name, "attempted": 1, "failed": 1}, ["*"]
		)
		self.assertFalse(failed_allocations)
		frappe.set_user("Administrator")
		frappe.get_doc("User", self.employee.user_id).remove_roles("HR Manager")

	def test_allocating_earned_leave_when_schedule_doesnt_exist(self):
		frappe.flags.current_date = get_year_start(getdate())
		employee1 = frappe.get_doc("Employee", "_T-Employee-00002")
		employee2 = frappe.copy_doc(employee1)
		employee2.user_id = None
		employee2.insert()
		leave_type = create_earned_leave_type(
			"Test Earned Leave", "First Day", 0.5, earned_leave_frequency="Monthly"
		)
		leave_period = create_leave_period(
			"Test Earned Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
		)
		leave_policy = frappe.get_doc(
			{
				"doctype": "Leave Policy",
				"title": "Test Earned Leave Policy",
				"leave_policy_details": [{"leave_type": leave_type.name, "annual_allocation": 24}],
			}
		).insert()

		data = {
			"assignment_based_on": "Leave Period",
			"leave_policy": leave_policy.name,
			"leave_period": leave_period.name,
			"carry_forward": 0,
			"effective_from": get_year_start(getdate()),
			"effective_to": get_year_ending(getdate()),
		}

		leave_policy_assignments = create_assignment_for_multiple_employees(
			[self.employee.name, employee1.name, employee2.name], frappe._dict(data)
		)
		leave_allocations = frappe.db.get_values(
			"Leave Allocation", {"employee": ("in", (employee1.name, employee2.name))}, pluck=True
		)
		frappe.db.delete("Earned Leave Schedule", {"parent": ("in", leave_allocations)})
		frappe.flags.current_date = add_months(get_year_start(getdate()), 1)
		allocate_earned_leaves()
		total_leaves_allocated_with_no_schedule = frappe.db.get_values(
			"Leave Allocation",
			{
				"employee": ("in", (employee1.name, employee2.name)),
				"leave_policy_assignment": ("in", leave_policy_assignments[1:]),
			},
			"total_leaves_allocated",
			pluck=True,
		)

		total_leaves_allocated_with_schedule = frappe.get_value(
			"Leave Allocation",
			{"employee": self.employee.name, "leave_policy_assignment": leave_policy_assignments[0]},
			"total_leaves_allocated",
		)
		self.assertEqual(total_leaves_allocated_with_no_schedule[0], 4)
		self.assertEqual(total_leaves_allocated_with_no_schedule[1], 4)
		self.assertEqual(total_leaves_allocated_with_schedule, 4)

		frappe.delete_doc_if_exists("Employee", employee2.name, force=1)

	def tearDown(self):
		frappe.db.set_value("Employee", self.employee.name, "date_of_joining", self.original_doj)
		frappe.db.set_value("Employee", "_T-Employee-00002", "date_of_joining", self.original_doj)
		frappe.db.set_value("Leave Type", self.leave_type, "max_leaves_allowed", 0)
		frappe.flags.current_date = None


def create_earned_leave_type(
	leave_type, allocate_on_day="Last Day", rounding=0.5, earned_leave_frequency="Monthly"
):
	frappe.delete_doc_if_exists("Leave Type", leave_type, force=1)
	frappe.delete_doc_if_exists("Leave Type", "Test Earned Leave Type", force=1)
	frappe.delete_doc_if_exists("Leave Type", "Test Earned Leave Type 2", force=1)

	return frappe.get_doc(
		leave_type_name=leave_type,
		doctype="Leave Type",
		is_earned_leave=1,
		earned_leave_frequency=earned_leave_frequency,
		rounding=rounding,
		is_carry_forward=1,
		allocate_on_day=allocate_on_day,
		max_leaves_allowed=0,
	).insert()


def create_leave_period(name, start_date=None, end_date=None):
	frappe.delete_doc_if_exists("Leave Period", name, force=1)

	if not start_date:
		start_date = get_first_day(getdate())

	return frappe.get_doc(
		name=name,
		doctype="Leave Period",
		from_date=start_date,
		to_date=end_date or add_months(start_date, 12),
		company="_Test Company",
		is_active=1,
	).insert()


def make_policy_assignment(
	employee,
	allocate_on_day="Last Day",
	rounding=0.5,
	earned_leave_frequency="Monthly",
	start_date=None,
	end_date=None,
	annual_allocation=12,
	carry_forward=0,
	assignment_based_on="Leave Period",
):
	leave_type = create_earned_leave_type(
		"Test Earned Leave", allocate_on_day, rounding, earned_leave_frequency=earned_leave_frequency
	)
	leave_period = create_leave_period("Test Earned Leave Period", start_date=start_date, end_date=end_date)
	leave_policy = frappe.get_doc(
		{
			"doctype": "Leave Policy",
			"title": "Test Earned Leave Policy",
			"leave_policy_details": [{"leave_type": leave_type.name, "annual_allocation": annual_allocation}],
		}
	).insert()

	data = {
		"assignment_based_on": assignment_based_on,
		"leave_policy": leave_policy.name,
		"leave_period": leave_period.name,
		"carry_forward": carry_forward,
		"effective_from": start_date,
		"effective_to": end_date,
	}

	leave_policy_assignments = create_assignment_for_multiple_employees([employee.name], frappe._dict(data))
	return leave_policy_assignments


def get_allocated_leaves(assignment):
	return frappe.db.get_value(
		"Leave Allocation",
		{"leave_policy_assignment": assignment},
		"total_leaves_allocated",
	)


def allocate_earned_leaves_for_months(months):
	for _ in range(0, months):
		frappe.flags.current_date = add_months(frappe.flags.current_date, 1)
		allocate_earned_leaves()
