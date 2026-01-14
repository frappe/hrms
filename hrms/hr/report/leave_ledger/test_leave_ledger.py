import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, add_months, flt, get_year_ending, get_year_start, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.holiday_list_assignment.test_holiday_list_assignment import (
	create_holiday_list_assignment,
)
from hrms.hr.doctype.leave_allocation.test_earned_leaves import (
	allocate_earned_leaves_for_months,
	create_earned_leave_type,
	make_policy_assignment,
)
from hrms.hr.doctype.leave_allocation.test_leave_allocation import create_leave_allocation
from hrms.hr.doctype.leave_application.test_leave_application import make_leave_application
from hrms.hr.doctype.leave_type.test_leave_type import create_leave_type
from hrms.hr.report.leave_ledger.leave_ledger import execute
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_holiday_list


class TestLeaveLedger(IntegrationTestCase):
	def setUp(self):
		for dt in [
			"Leave Application",
			"Leave Allocation",
			"Leave Ledger Entry",
			"Leave Period",
		]:
			frappe.db.delete(dt)

		frappe.db.delete("Employee", {"company": "_Test Company"})

		self.date = getdate()
		self.year_start = getdate(get_year_start(self.date))
		self.year_end = getdate(get_year_ending(self.date))

		holiday_list = make_holiday_list(
			"_Test Emp Balance Holiday List",
			self.year_start,
			self.year_end,
			add_weekly_offs=False,
		)
		self.employee_1 = frappe.get_doc(
			"Employee", make_employee("test_emp_1@example.com", company="_Test Company")
		)
		create_holiday_list_assignment("Employee", self.employee_1.name, holiday_list)
		self.employee_2 = frappe.get_doc(
			"Employee", make_employee("test_emp_2@example.com", company="_Test Company")
		)
		create_holiday_list_assignment("Employee", self.employee_2.name, holiday_list)

		# create leave type
		self.earned_leave = "Test Earned Leave"
		self.casual_leave = "_Test Leave Type"
		create_leave_type(leave_type=self.earned_leave)
		create_leave_type(leave_type=self.casual_leave)

		self.create_earned_leave_allocation()
		self.create_casual_leave_allocation()
		self.create_leave_applications()

	def create_earned_leave_allocation(self):
		# emp 1 - earned leave allocation
		frappe.flags.current_date = add_months(self.year_start, 2)
		# 3 leaves allocated
		assignments = make_policy_assignment(
			self.employee_1,
			annual_allocation=12,
			allocate_on_day="First Day",
			start_date=self.year_start,
			end_date=self.year_end,
		)

		# 7 more leaves allocated in the subsequent months
		allocate_earned_leaves_for_months(1)

		allocation = frappe.db.get_value(
			"Leave Allocation", {"leave_policy_assignment": assignments[0]}, "name"
		)
		self.earned_leave_allocation = frappe.get_doc("Leave Allocation", allocation)

	def create_casual_leave_allocation(self):
		allocation = create_leave_allocation(
			leave_type=self.casual_leave,
			employee=self.employee_2.name,
			from_date=self.year_start,
			to_date=self.year_end,
		)
		allocation.submit()
		self.casual_leave_allocation = allocation

	def create_leave_applications(self):
		from_date = add_months(self.year_start, 2)
		to_date = add_days(from_date, 1)
		self.earned_leave_appl_1 = make_leave_application(
			self.employee_1.name, from_date, to_date, self.earned_leave
		)

		self.casual_leave_appl_2 = make_leave_application(
			self.employee_2.name, from_date, to_date, self.casual_leave
		)

	def test_report_with_filters(self):
		filters = frappe._dict(
			{
				"from_date": self.year_start,
				"to_date": self.year_end,
				"employee": self.employee_1.name,
				"leave_type": self.earned_leave,
			}
		)

		report = execute(filters)
		result = report[1][:-1]

		self.assertTrue(all(row.employee == self.employee_1.name for row in result))
		self.assertTrue(all(row.leave_type == self.earned_leave for row in result))

		actual_result = []
		for row in result:
			actual_result.append(
				{
					"transaction_type": row.transaction_type,
					"transaction_name": row.transaction_name,
					"leaves": row.leaves,
				}
			)

		expected_result = [
			{
				"transaction_type": "Leave Allocation",
				"transaction_name": self.earned_leave_allocation.name,
				"leaves": 3,
			},
			{
				"transaction_type": "Leave Application",
				"transaction_name": self.earned_leave_appl_1.name,
				"leaves": -2,
			},
			{
				"transaction_type": "Leave Allocation",
				"transaction_name": self.earned_leave_allocation.name,
				"leaves": 1,
			},
		]

		self.assertEqual(actual_result, expected_result)

	def test_totals(self):
		def get_total_row(filters):
			report = execute(filters)
			return report[1][-1]

		# CASE 1: no filters, skip total row
		filters = frappe._dict(
			{
				"from_date": self.year_start,
				"to_date": self.year_end,
			}
		)

		total_row = get_total_row(filters)
		self.assertNotIn("Total", total_row.employee)

		# CASE 2: employee filter, add total row
		filters = frappe._dict(
			{
				"from_date": self.year_start,
				"to_date": self.year_end,
				"employee": self.employee_1.name,
			}
		)

		total_row = get_total_row(filters)
		self.assertIn(f"Total Leaves ({self.earned_leave})", total_row.employee)
		# 4 leaves allocated, 2 leaves taken
		self.assertEqual(total_row.leaves, 2)

		# CASE 3: leave type filter with only 1 allocation, add total row
		filters = frappe._dict(
			{
				"from_date": self.year_start,
				"to_date": self.year_end,
				"leave_type": self.casual_leave,
			}
		)

		total_row = get_total_row(filters)
		self.assertEqual(f"Total Leaves ({self.casual_leave})", total_row.employee)
		# 15 leave allocated, 2 leave taken
		self.assertEqual(total_row.leaves, 13)

	def tearDown(self):
		frappe.flags.current_date = None
