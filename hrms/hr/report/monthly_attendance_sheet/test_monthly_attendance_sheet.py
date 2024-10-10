from dateutil.relativedelta import relativedelta

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import get_year_ending, get_year_start, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee
from erpnext.setup.doctype.holiday_list.test_holiday_list import set_holiday_list

from hrms.hr.doctype.attendance.attendance import mark_attendance
from hrms.hr.doctype.leave_application.test_leave_application import make_allocation_record
from hrms.hr.doctype.shift_type.test_shift_type import setup_shift_type
from hrms.hr.report.monthly_attendance_sheet.monthly_attendance_sheet import execute
from hrms.payroll.doctype.salary_slip.test_salary_slip import (
	make_holiday_list,
	make_leave_application,
)
from hrms.tests.test_utils import create_company, get_first_day_for_prev_month


class TestMonthlyAttendanceSheet(IntegrationTestCase):
	def setUp(self):
		self.company = "_Test Company"
		self.employee = make_employee("test_employee@example.com", company=self.company)
		frappe.db.delete("Attendance")

		if not frappe.db.exists("Shift Type", "Day Shift"):
			setup_shift_type(shift_type="Day Shift")

		date = getdate()
		from_date = get_year_start(date)
		to_date = get_year_ending(date)
		make_holiday_list(from_date=from_date, to_date=to_date)

	@set_holiday_list("Salary Slip Test Holiday List", "_Test Company")
	def test_monthly_attendance_sheet_report(self):
		previous_month_first = get_first_day_for_prev_month()

		# mark different attendance status on first 3 days of previous month
		mark_attendance(self.employee, previous_month_first, "Absent")
		mark_attendance(self.employee, previous_month_first + relativedelta(days=1), "Present")
		mark_attendance(self.employee, previous_month_first + relativedelta(days=2), "On Leave")

		employee_on_leave_with_shift = make_employee("employee@leave.com", company=self.company)
		mark_attendance(employee_on_leave_with_shift, previous_month_first, "On Leave", "Day Shift")

		filters = frappe._dict(
			{
				"month": previous_month_first.month,
				"year": previous_month_first.year,
				"company": self.company,
			}
		)
		report = execute(filters=filters)

		datasets = report[3]["data"]["datasets"]
		absent = datasets[0]["values"]
		present = datasets[1]["values"]
		leaves = datasets[2]["values"]

		# ensure correct attendance is reflected on the report
		self.assertEqual(self.employee, report[1][0].get("employee"))
		self.assertEqual("Day Shift", report[1][1].get("shift"))
		self.assertEqual(absent[0], 1)
		self.assertEqual(present[1], 1)
		self.assertEqual(leaves[2], 1)

	@set_holiday_list("Salary Slip Test Holiday List", "_Test Company")
	def test_detailed_view(self):
		previous_month_first = get_first_day_for_prev_month()

		# attendance with shift
		mark_attendance(self.employee, previous_month_first, "Absent", "Day Shift")
		mark_attendance(self.employee, previous_month_first + relativedelta(days=1), "Present", "Day Shift")

		# attendance without shift
		mark_attendance(self.employee, previous_month_first + relativedelta(days=2), "On Leave")
		mark_attendance(self.employee, previous_month_first + relativedelta(days=3), "Present")

		filters = frappe._dict(
			{
				"month": previous_month_first.month,
				"year": previous_month_first.year,
				"company": self.company,
			}
		)
		report = execute(filters=filters)

		day_shift_row = report[1][0]
		row_without_shift = report[1][1]

		self.assertEqual(day_shift_row["shift"], "Day Shift")
		self.assertEqual(day_shift_row["1"], "A")  # absent on the 1st day of the month
		self.assertEqual(day_shift_row["2"], "P")  # present on the 2nd day

		self.assertEqual(row_without_shift["shift"], "")
		self.assertEqual(row_without_shift["4"], "P")  # present on the 4th day

		# leave should be shown against every shift
		self.assertTrue(day_shift_row["3"] == row_without_shift["3"] == "L")

	@set_holiday_list("Salary Slip Test Holiday List", "_Test Company")
	def test_single_shift_with_leaves_in_detailed_view(self):
		previous_month_first = get_first_day_for_prev_month()

		# attendance with shift
		mark_attendance(self.employee, previous_month_first, "Absent", "Day Shift")
		mark_attendance(self.employee, previous_month_first + relativedelta(days=1), "Present", "Day Shift")

		# attendance without shift
		mark_attendance(self.employee, previous_month_first + relativedelta(days=2), "On Leave")

		filters = frappe._dict(
			{
				"month": previous_month_first.month,
				"year": previous_month_first.year,
				"company": self.company,
			}
		)
		report = execute(filters=filters)
		# do not split for leave record
		self.assertEqual(len(report[1]), 1)

		day_shift_row = report[1][0]

		self.assertEqual(day_shift_row["shift"], "Day Shift")
		self.assertEqual(day_shift_row["1"], "A")  # absent on the 1st day of the month
		self.assertEqual(day_shift_row["2"], "P")  # present on the 2nd day
		self.assertEqual(day_shift_row["3"], "L")  # leave on the 3rd day

	@set_holiday_list("Salary Slip Test Holiday List", "_Test Company")
	def test_single_leave_record(self):
		previous_month_first = get_first_day_for_prev_month()

		# attendance without shift
		mark_attendance(self.employee, previous_month_first, "On Leave")

		filters = frappe._dict(
			{
				"month": previous_month_first.month,
				"year": previous_month_first.year,
				"company": self.company,
			}
		)
		report = execute(filters=filters)

		# single row with leave record
		self.assertEqual(len(report[1]), 1)
		row = report[1][0]

		self.assertIsNone(row["shift"])
		self.assertEqual(row["1"], "L")

	@set_holiday_list("Salary Slip Test Holiday List", "_Test Company")
	def test_summarized_view(self):
		previous_month_first = get_first_day_for_prev_month()

		# attendance with shift
		mark_attendance(self.employee, previous_month_first, "Absent", "Day Shift")
		mark_attendance(self.employee, previous_month_first + relativedelta(days=1), "Present", "Day Shift")
		mark_attendance(self.employee, previous_month_first + relativedelta(days=2), "Half Day")  # half day

		mark_attendance(
			self.employee, previous_month_first + relativedelta(days=3), "Present"
		)  # attendance without shift
		mark_attendance(
			self.employee, previous_month_first + relativedelta(days=4), "Present", late_entry=1
		)  # late entry
		mark_attendance(
			self.employee, previous_month_first + relativedelta(days=5), "Present", early_exit=1
		)  # early exit

		leave_application = get_leave_application(self.employee)

		filters = frappe._dict(
			{
				"month": previous_month_first.month,
				"year": previous_month_first.year,
				"company": self.company,
				"summarized_view": 1,
			}
		)
		report = execute(filters=filters)

		row = report[1][0]
		self.assertEqual(row["employee"], self.employee)

		# 4 present + half day absent 0.5
		self.assertEqual(row["total_present"], 4.5)
		# 1 present
		self.assertEqual(row["total_absent"], 1)
		# leave days + half day leave 0.5
		self.assertEqual(row["total_leaves"], leave_application.total_leave_days + 0.5)

		self.assertEqual(row["_test_leave_type"], leave_application.total_leave_days)
		self.assertEqual(row["total_late_entries"], 1)
		self.assertEqual(row["total_early_exits"], 1)

	@set_holiday_list("Salary Slip Test Holiday List", "_Test Company")
	def test_attendance_with_group_by_filter(self):
		previous_month_first = get_first_day_for_prev_month()

		# attendance with shift
		mark_attendance(self.employee, previous_month_first, "Absent", "Day Shift")
		mark_attendance(self.employee, previous_month_first + relativedelta(days=1), "Present", "Day Shift")

		# attendance without shift
		mark_attendance(self.employee, previous_month_first + relativedelta(days=2), "On Leave")
		mark_attendance(self.employee, previous_month_first + relativedelta(days=3), "Present")

		departmentless_employee = make_employee(
			"emp@departmentless.com", company=self.company, department=None
		)
		mark_attendance(departmentless_employee, previous_month_first + relativedelta(days=3), "Present")

		filters = frappe._dict(
			{
				"month": previous_month_first.month,
				"year": previous_month_first.year,
				"company": self.company,
				"group_by": "Department",
			}
		)
		report = execute(filters=filters)

		department = frappe.db.get_value("Employee", self.employee, "department")
		department_row = report[1][0]
		self.assertIn(department, department_row["department"])

		day_shift_row = report[1][1]
		row_without_shift = report[1][2]

		self.assertEqual(day_shift_row["shift"], "Day Shift")
		self.assertEqual(day_shift_row["1"], "A")  # absent on the 1st day of the month
		self.assertEqual(day_shift_row["2"], "P")  # present on the 2nd day

		self.assertEqual(row_without_shift["shift"], "")
		self.assertEqual(row_without_shift["3"], "L")  # on leave on the 3rd day
		self.assertEqual(row_without_shift["4"], "P")  # present on the 4th day

	def test_attendance_with_employee_filter(self):
		previous_month_first = get_first_day_for_prev_month()

		employee2 = make_employee("test_employee2@example.com", company=self.company)
		employee3 = make_employee("test_employee3@example.com", company=self.company)

		# mark different attendance status on first 3 days of previous month for employee1
		mark_attendance(self.employee, previous_month_first, "Absent")
		mark_attendance(self.employee, previous_month_first + relativedelta(days=1), "Present")
		mark_attendance(self.employee, previous_month_first + relativedelta(days=2), "On Leave")

		# mark different attendance status on first 3 days of previous month for employee2
		mark_attendance(employee2, previous_month_first, "Absent")
		mark_attendance(employee2, previous_month_first + relativedelta(days=1), "Present")
		mark_attendance(employee2, previous_month_first + relativedelta(days=2), "On Leave")

		# mark different attendance status on first 3 days of previous month for employee3
		mark_attendance(employee3, previous_month_first, "Absent")
		mark_attendance(employee3, previous_month_first + relativedelta(days=1), "Present")
		mark_attendance(employee3, previous_month_first + relativedelta(days=2), "On Leave")

		filters = frappe._dict(
			{
				"month": previous_month_first.month,
				"year": previous_month_first.year,
				"company": self.company,
				"employee": self.employee,
			}
		)
		report = execute(filters=filters)

		record = report[1][0]
		datasets = report[3]["data"]["datasets"]
		absent = datasets[0]["values"]
		present = datasets[1]["values"]
		leaves = datasets[2]["values"]

		# ensure that only show the attendance for the specified employee
		self.assertEqual(len(report[1]), 1)

		# ensure correct attendance is reflected on the report
		self.assertEqual(self.employee, record.get("employee"))
		self.assertEqual(absent[0], 1)
		self.assertEqual(present[1], 1)
		self.assertEqual(leaves[2], 1)

	def test_attendance_with_company_filter(self):
		create_company("Test Parent Company", is_group=1)
		create_company("Test Child Company", is_group=1, parent_company="Test Parent Company")
		create_company("Test Grandchild Company", parent_company="Test Child Company")

		employee1 = make_employee("test_employee@parent.com", company="Test Parent Company")
		employee2 = make_employee("test_employee@child.com", company="Test Child Company")
		employee3 = make_employee("test_employee@grandchild.com", company="Test Grandchild Company")

		previous_month_first = get_first_day_for_prev_month()
		mark_attendance(employee1, previous_month_first, "Present")
		mark_attendance(employee2, previous_month_first, "Present")
		mark_attendance(employee3, previous_month_first, "Present")

		filters = frappe._dict(
			{
				"month": previous_month_first.month,
				"year": previous_month_first.year,
				"company": "Test Parent Company",
				"include_company_descendants": 1,
			}
		)
		report = execute(filters=filters)
		self.assertEqual(len(report[1]), 3)

		filters.include_company_descendants = 0
		report = execute(filters=filters)
		self.assertEqual(len(report[1]), 1)

	def test_attendance_with_employee_filter_and_summarized_view(self):
		previous_month_first = get_first_day_for_prev_month()

		employee2 = make_employee("test_employee2@example.com", company=self.company)
		employee3 = make_employee("test_employee3@example.com", company=self.company)

		# mark different attendance status on first 3 days of previous month for employee1
		mark_attendance(self.employee, previous_month_first, "Absent")
		mark_attendance(self.employee, previous_month_first + relativedelta(days=1), "Present")
		mark_attendance(self.employee, previous_month_first + relativedelta(days=2), "On Leave")

		# mark different attendance status on first 3 days of previous month for employee2
		mark_attendance(employee2, previous_month_first, "Absent")
		mark_attendance(employee2, previous_month_first + relativedelta(days=1), "Present")
		mark_attendance(employee2, previous_month_first + relativedelta(days=2), "On Leave")

		# mark different attendance status on first 3 days of previous month for employee3
		mark_attendance(employee3, previous_month_first, "Absent")
		mark_attendance(employee3, previous_month_first + relativedelta(days=1), "Present")
		mark_attendance(employee3, previous_month_first + relativedelta(days=2), "On Leave")

		filters = frappe._dict(
			{
				"month": previous_month_first.month,
				"year": previous_month_first.year,
				"company": self.company,
				"employee": self.employee,
				"summarized_view": 1,
			}
		)
		report = execute(filters=filters)

		record = report[1][0]
		datasets = report[3]["data"]["datasets"]
		absent = datasets[0]["values"]
		present = datasets[1]["values"]
		leaves = datasets[2]["values"]

		# ensure that only show the attendance for the specified employee
		self.assertEqual(len(report[1]), 1)

		# ensure correct attendance is reflected on the report
		self.assertEqual(self.employee, record.get("employee"))
		self.assertEqual(absent[0], 1)
		self.assertEqual(present[1], 1)
		self.assertEqual(leaves[2], 1)

	@set_holiday_list("Salary Slip Test Holiday List", "_Test Company")
	def test_validations(self):
		# validation error for filters without month and year
		self.assertRaises(frappe.ValidationError, execute_report_with_invalid_filters)

		# execute report without attendance record
		previous_month_first = get_first_day_for_prev_month()

		filters = frappe._dict(
			{
				"month": previous_month_first.month,
				"year": previous_month_first.year,
				"company": self.company,
				"group_by": "Department",
			}
		)
		report = execute(filters=filters)
		self.assertEqual(report, ([], [], None, None))


def get_leave_application(employee):
	previous_month_first = get_first_day_for_prev_month()

	year_start = getdate(get_year_start(previous_month_first))
	year_end = getdate(get_year_ending(previous_month_first))

	make_allocation_record(employee=employee, from_date=year_start, to_date=year_end)

	from_date = previous_month_first.replace(day=7)
	to_date = previous_month_first.replace(day=8)

	return make_leave_application(employee, from_date, to_date, "_Test Leave Type")


def execute_report_with_invalid_filters():
	filters = frappe._dict({"company": "_Test Company", "group_by": "Department"})
	execute(filters=filters)
