import calendar
from datetime import date

import frappe
from frappe.utils import add_months, get_first_day, get_last_day, get_year_ending, get_year_start, getdate

from hrms.hr.doctype.leave_allocation.test_earned_leaves import make_policy_assignment
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_holiday_list
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

		self.employee = employee
		self.leave_type = "Test Earned Leave"

		from_date = get_year_start(getdate())
		to_date = get_year_ending(getdate())
		self.holiday_list = make_holiday_list(from_date=from_date, to_date=to_date)
		frappe.db.set_value("Email Account", "_Test Email Account 1", "default_outgoing", 1)

	def tearDown(self):
		frappe.db.set_value("Employee", self.employee.name, "date_of_joining", self.original_doj)
		frappe.db.set_value("Leave Type", self.leave_type, "max_leaves_allowed", 0)
		frappe.flags.current_date = None

	def test_schedule_for_monthly_earned_leave_allocated_on_first_day(self):
		frappe.flags.current_date = get_year_start(getdate())
		earned_leave_schedule = create_earned_leave_schedule(
			self.employee,
			allocate_on_day="First Day",
			earned_leave_frequency="Monthly",
			annual_allocation=24,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
		)
		allocation_dates = [allocation.allocation_date for allocation in earned_leave_schedule]
		self.assertEqual(len(earned_leave_schedule), 12)
		self.assertEqual(earned_leave_schedule[0].number_of_leaves, 2)
		test_allocation_dates(
			self,
			allocation_dates,
			get_year_start(getdate()),
			get_year_ending(getdate()),
			"Monthly",
			"First Day",
		)

	def test_schedule_for_monthly_earned_leave_allocated_on_last_day(self):
		frappe.flags.current_date = get_year_start(getdate())
		earned_leave_schedule = create_earned_leave_schedule(
			self.employee,
			allocate_on_day="Last Day",
			earned_leave_frequency="Monthly",
			annual_allocation=24,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
		)
		allocation_dates = [allocation.allocation_date for allocation in earned_leave_schedule]
		self.assertEqual(len(earned_leave_schedule), 12)
		self.assertEqual(earned_leave_schedule[0].number_of_leaves, 2)
		test_allocation_dates(
			self,
			allocation_dates,
			get_year_start(getdate()),
			get_year_ending(getdate()),
			"Monthly",
			"Last Day",
		)

	def test_schedule_for_monthly_earned_leave_allocated_on_doj(self):
		frappe.flags.current_date = get_year_start(getdate())
		earned_leave_schedule = create_earned_leave_schedule(
			self.employee,
			allocate_on_day="Date of Joining",
			earned_leave_frequency="Monthly",
			annual_allocation=24,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
		)
		allocation_dates = [allocation.allocation_date for allocation in earned_leave_schedule]
		self.assertEqual(len(earned_leave_schedule), 12)
		self.assertEqual(earned_leave_schedule[0].number_of_leaves, 2)
		test_allocation_dates(
			self,
			allocation_dates,
			get_year_start(getdate()),
			get_year_ending(getdate()),
			"Monthly",
			"Date of Joining",
			self.employee.date_of_joining,
		)

	def test_schedule_for_quaterly_earned_leave_allocated_on_first_day(self):
		frappe.flags.current_date = get_year_start(getdate())
		earned_leave_schedule = create_earned_leave_schedule(
			self.employee,
			allocate_on_day="First Day",
			earned_leave_frequency="Quarterly",
			annual_allocation=24,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
		)
		allocation_dates = [allocation.allocation_date for allocation in earned_leave_schedule]
		self.assertEqual(len(earned_leave_schedule), 4)
		self.assertEqual(earned_leave_schedule[0].number_of_leaves, 6)
		test_allocation_dates(
			self,
			allocation_dates,
			get_year_start(getdate()),
			get_year_ending(getdate()),
			"Quarterly",
			"First Day",
		)

	def test_schedule_for_quaterly_earned_leave_allocated_on_last_day(self):
		frappe.flags.current_date = get_year_start(getdate())
		earned_leave_schedule = create_earned_leave_schedule(
			self.employee,
			allocate_on_day="Last Day",
			earned_leave_frequency="Quarterly",
			annual_allocation=24,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
		)
		allocation_dates = [allocation.allocation_date for allocation in earned_leave_schedule]
		self.assertEqual(len(earned_leave_schedule), 4)
		self.assertEqual(earned_leave_schedule[0].number_of_leaves, 6)
		test_allocation_dates(
			self,
			allocation_dates,
			get_year_start(getdate()),
			get_year_ending(getdate()),
			"Quarterly",
			"Last Day",
		)

	def test_schedule_for_half_yearly_earned_leave_allocated_on_first_day(self):
		frappe.flags.current_date = get_year_start(getdate())
		earned_leave_schedule = create_earned_leave_schedule(
			self.employee,
			allocate_on_day="First Day",
			earned_leave_frequency="Half-Yearly",
			annual_allocation=24,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
		)

		allocation_dates = [allocation.allocation_date for allocation in earned_leave_schedule]
		self.assertEqual(len(earned_leave_schedule), 2)
		self.assertEqual(earned_leave_schedule[0].number_of_leaves, 12)
		test_allocation_dates(
			self,
			allocation_dates,
			get_year_start(getdate()),
			get_year_ending(getdate()),
			"Half-Yearly",
			"First Day",
		)

	def test_schedule_for_half_yearly_earned_leave_allocated_on_last_day(self):
		frappe.flags.current_date = get_year_start(getdate())
		earned_leave_schedule = create_earned_leave_schedule(
			self.employee,
			allocate_on_day="Last Day",
			earned_leave_frequency="Half-Yearly",
			annual_allocation=24,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
		)
		allocation_dates = [allocation.allocation_date for allocation in earned_leave_schedule]
		self.assertEqual(len(earned_leave_schedule), 2)
		self.assertEqual(earned_leave_schedule[0].number_of_leaves, 12)
		test_allocation_dates(
			self,
			allocation_dates,
			get_year_start(getdate()),
			get_year_ending(getdate()),
			"Half-Yearly",
			"Last Day",
		)

	def test_schedule_for_yearly_earned_leave_allocated_on_first_day(self):
		frappe.flags.current_date = get_year_start(getdate())
		earned_leave_schedule = create_earned_leave_schedule(
			self.employee,
			allocate_on_day="First Day",
			earned_leave_frequency="Yearly",
			annual_allocation=24,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=add_months(get_year_ending(getdate()), 12),
		)
		allocation_dates = [allocation.allocation_date for allocation in earned_leave_schedule]
		self.assertEqual(len(earned_leave_schedule), 2)
		self.assertEqual(earned_leave_schedule[0].number_of_leaves, 24)
		test_allocation_dates(
			self,
			allocation_dates,
			get_year_start(getdate()),
			add_months(get_year_ending(getdate()), 12),
			"Yearly",
			"First Day",
		)

	def test_schedule_for_yearly_earned_leave_allocated_on_last_day(self):
		frappe.flags.current_date = get_year_start(getdate())
		earned_leave_schedule = create_earned_leave_schedule(
			self.employee,
			allocate_on_day="Last Day",
			earned_leave_frequency="Yearly",
			annual_allocation=24,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=add_months(get_year_ending(getdate()), 12),
		)
		allocation_dates = [allocation.allocation_date for allocation in earned_leave_schedule]
		self.assertEqual(len(earned_leave_schedule), 2)
		self.assertEqual(earned_leave_schedule[0].number_of_leaves, 24)
		test_allocation_dates(
			self,
			allocation_dates,
			get_year_start(getdate()),
			add_months(get_year_ending(getdate()), 12),
			"Yearly",
			"Last Day",
		)

	def test_schedule_when_doj_is_in_the_middle_of_leave_period(self):
		self.employee.date_of_joining = add_months(get_year_start(getdate()), 4)
		self.employee.save()
		frappe.flags.current_date = add_months(get_year_start(getdate()), 4)
		earned_leave_schedule = create_earned_leave_schedule(
			self.employee,
			allocate_on_day="First Day",
			earned_leave_frequency="Quarterly",
			annual_allocation=24,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
		)

		self.assertEqual(len(earned_leave_schedule), 3)
		self.assertEqual(earned_leave_schedule[0].number_of_leaves, 4)
		self.assertEqual(earned_leave_schedule[0].allocation_date, add_months(get_year_start(getdate()), 4))
		self.assertEqual(earned_leave_schedule[1].number_of_leaves, 6)
		self.assertEqual(earned_leave_schedule[1].allocation_date, add_months(get_year_start(getdate()), 6))

	def test_schedule_when_assignment_is_based_on_doj(self):
		self.employee.date_of_joining = add_months(get_year_start(getdate()), 4)
		self.employee.save()
		frappe.flags.current_date = add_months(get_year_start(getdate()), 4)
		earned_leave_schedule = create_earned_leave_schedule(
			self.employee,
			allocate_on_day="First Day",
			earned_leave_frequency="Quarterly",
			annual_allocation=24,
			assignment_based_on="Joining Date",
			start_date=add_months(get_year_start(getdate()), 4),
			end_date=get_year_ending(getdate()),
		)

		self.assertEqual(len(earned_leave_schedule), 3)
		self.assertEqual(earned_leave_schedule[0].number_of_leaves, 4)
		self.assertEqual(earned_leave_schedule[0].allocation_date, add_months(get_year_start(getdate()), 4))
		self.assertEqual(earned_leave_schedule[1].number_of_leaves, 6)
		self.assertEqual(earned_leave_schedule[1].allocation_date, add_months(get_year_start(getdate()), 6))

	def test_schedule_when_leave_policy_is_assigned_in_middle_of_the_period_allocated_on_first_day(self):
		frappe.flags.current_date = add_months(get_year_start(getdate()), 4)
		earned_leave_schedule = create_earned_leave_schedule(
			self.employee,
			allocate_on_day="First Day",
			earned_leave_frequency="Quarterly",
			annual_allocation=24,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
		)

		self.assertEqual(len(earned_leave_schedule), 3)
		self.assertEqual(earned_leave_schedule[0].number_of_leaves, 12)
		self.assertEqual(earned_leave_schedule[0].allocation_date, add_months(get_year_start(getdate()), 4))
		self.assertEqual(earned_leave_schedule[1].number_of_leaves, 6)
		self.assertEqual(earned_leave_schedule[1].allocation_date, add_months(get_year_start(getdate()), 6))

	def test_schedule_when_leave_policy_is_assigned_in_middle_of_the_period_allocated_on_last_day(self):
		frappe.flags.current_date = get_last_day(add_months(get_year_start(getdate()), 7))
		earned_leave_schedule = create_earned_leave_schedule(
			self.employee,
			allocate_on_day="Last Day",
			earned_leave_frequency="Quarterly",
			annual_allocation=24,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
		)

		self.assertEqual(len(earned_leave_schedule), 3)
		self.assertEqual(earned_leave_schedule[0].number_of_leaves, 12)
		self.assertEqual(earned_leave_schedule[0].allocation_date, frappe.flags.current_date)
		self.assertEqual(earned_leave_schedule[1].number_of_leaves, 6)
		self.assertEqual(earned_leave_schedule[1].allocation_date, add_months(get_year_ending(getdate()), -3))

	def test_schedule_when_doj_is_end_of_big_month(self):
		frappe.flags.current_date = get_year_start(getdate())
		self.employee.date_of_joining = get_last_day(get_year_start(getdate()))
		self.employee.save()
		earned_leave_schedule = create_earned_leave_schedule(
			self.employee,
			allocate_on_day="Date of Joining",
			earned_leave_frequency="Monthly",
			annual_allocation=24,
			assignment_based_on="Leave Period",
			start_date=get_year_start(getdate()),
			end_date=get_year_ending(getdate()),
		)
		allocation_dates = [allocation.allocation_date for allocation in earned_leave_schedule]
		self.assertEqual(len(earned_leave_schedule), 12)
		# prorated leave is 0 because the employee just joined
		self.assertEqual(earned_leave_schedule[0].number_of_leaves, 0)
		self.assertEqual(earned_leave_schedule[1].number_of_leaves, 2)
		test_allocation_dates(
			self,
			allocation_dates,
			get_year_start(getdate()),
			get_year_ending(getdate()),
			"Monthly",
			"Last Day",
			self.employee.date_of_joining,
		)

	def test_absence_of_earned_leave_schedule_for_non_earned_leave_types(self):
		leave_policy = frappe.get_doc(
			{
				"doctype": "Leave Policy",
				"title": "Test Earned Leave Policy",
				"leave_policy_details": [{"leave_type": self.leave_types[0].name, "annual_allocation": 12}],
			}
		).insert()

		data = {
			"employee": self.employee.name,
			"leave_policy": leave_policy.name,
			"effective_from": get_year_start(getdate()),
			"effective_to": get_year_ending(getdate()),
		}

		leave_policy_assignment = frappe.new_doc("Leave Policy Assignment", **frappe._dict(data))
		leave_policy_assignment.insert()
		leave_policy_assignment.submit()

		leave_allocation = frappe.get_doc(
			"Leave Allocation", {"leave_policy_assignment": leave_policy_assignment.name}
		)
		self.assertEqual(leave_allocation.total_leaves_allocated, 12)
		self.assertFalse(leave_allocation.earned_leave_schedule)


def test_allocation_dates(
	self,
	allocation_dates,
	start_date,
	end_date,
	earned_leave_frequency,
	allocate_on_day,
	date_of_joining=None,
):
	schedule_map = {
		"Monthly": {
			"First Day": get_first_days_of_the_months(start_date, end_date),
			"Last Day": get_last_days_of_the_months(start_date, end_date),
			"Date of Joining": get_doj_for_months(date_of_joining, start_date, end_date),
		},
		"Quarterly": {
			"First Day": get_first_days_of_quarters(start_date, end_date),
			"Last Day": get_last_days_of_quarters(start_date, end_date),
		},
		"Half-Yearly": {
			"First Day": get_first_days_of_half_years(start_date, end_date),
			"Last Day": get_last_days_of_half_years(start_date, end_date),
		},
		"Yearly": {
			"First Day": get_first_days_of_years(start_date, end_date),
			"Last Day": get_last_days_of_years(start_date, end_date),
		},
	}

	for dt, de in zip(allocation_dates, schedule_map[earned_leave_frequency][allocate_on_day], strict=True):
		self.assertEqual(dt, de)


def create_earned_leave_schedule(
	employee,
	allocate_on_day,
	earned_leave_frequency,
	annual_allocation,
	assignment_based_on,
	start_date,
	end_date,
):
	assignment = make_policy_assignment(
		employee,
		allocate_on_day=allocate_on_day,
		earned_leave_frequency=earned_leave_frequency,
		annual_allocation=annual_allocation,
		assignment_based_on=assignment_based_on,
		start_date=start_date,
		end_date=end_date,
	)[0]
	leave_allocation = frappe.get_value("Leave Allocation", {"leave_policy_assignment": assignment}, "name")
	earned_leave_schedule = frappe.get_all(
		"Earned Leave Schedule",
		{"parent": leave_allocation},
		["allocation_date", "number_of_leaves", "allocated_via", "attempted", "is_allocated"],
		order_by="allocation_date",
	)
	return earned_leave_schedule


def get_first_days_of_the_months(start_date, end_date):
	year_range = range(start_date.year, end_date.year + 1)
	return [date(year, month, 1) for year in year_range for month in range(1, 13)]


def get_last_days_of_the_months(start_date, end_date):
	year_range = range(start_date.year, end_date.year + 1)
	return [
		date(year, month, calendar.monthrange(year, month)[1])
		for year in year_range
		for month in range(1, 13)
	]


def get_doj_for_months(date_of_joining, start_date, end_date):
	if not date_of_joining:
		return
	year_range = range(start_date.year, end_date.year + 1)
	return [
		date(year, month, min(date_of_joining.day, calendar.monthrange(year, month)[1]))
		for year in year_range
		for month in range(1, 13)
	]


def get_first_days_of_quarters(start_date, end_date):
	year_range = range(start_date.year, end_date.year + 1)
	return [date(year, month, 1) for year in year_range for month in (1, 4, 7, 10)]


def get_last_days_of_quarters(start_date, end_date):
	year_range = range(start_date.year, end_date.year + 1)
	return [
		date(year, month, calendar.monthrange(year, month)[1])
		for year in year_range
		for month in (3, 6, 9, 12)
	]


def get_first_days_of_half_years(start_date, end_date):
	year_range = range(start_date.year, end_date.year + 1)
	return [date(year, month, 1) for year in year_range for month in (1, 7)]


def get_last_days_of_half_years(start_date, end_date):
	year_range = range(start_date.year, end_date.year + 1)
	return [
		date(year, month, calendar.monthrange(year, month)[1]) for year in year_range for month in (6, 12)
	]


def get_first_days_of_years(start_date, end_date):
	year_range = range(start_date.year, end_date.year + 1)
	return [date(year, 1, 1) for year in year_range]


def get_last_days_of_years(start_date, end_date):
	year_range = range(start_date.year, end_date.year + 1)
	return [date(year, 12, calendar.monthrange(year, 12)[1]) for year in year_range]
