from dateutil.relativedelta import relativedelta

import frappe
from frappe.utils import add_days, get_year_ending, get_year_start, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.attendance.attendance import mark_attendance
from hrms.hr.doctype.holiday_list_assignment.test_holiday_list_assignment import (
	create_holiday_list_assignment,
)
from hrms.hr.report.employees_working_on_a_holiday.employees_working_on_a_holiday import execute
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_holiday_list
from hrms.tests.test_utils import add_date_to_holiday_list, get_first_sunday
from hrms.tests.utils import HRMSTestSuite


class TestEmployeesWorkingOnAHoliday(HRMSTestSuite):
	def setUp(self):
		self.company = "_Test Company"
		frappe.db.delete("Attendance")

	def test_report(self):
		date = getdate()
		from_date = get_year_start(date)
		to_date = get_year_ending(date)
		sunday_off = make_holiday_list("Sunday Off", from_date, to_date, True)
		monday_off = make_holiday_list("Monday Off", from_date, to_date, True, ["Monday"])
		tuesday_off = make_holiday_list("Tuesday Off", from_date, to_date, True, ["Tuesday"])

		emp1 = make_employee("testemp@sunday.com", company=self.company)
		create_holiday_list_assignment("Employee", emp1, sunday_off)
		emp2 = make_employee("testemp2@monday.com", company=self.company)
		create_holiday_list_assignment("Employee", emp2, monday_off)
		emp3 = make_employee("testemp3@tuesday.com", company=self.company)
		create_holiday_list_assignment("Employee", emp3, tuesday_off)

		first_sunday = get_first_sunday()
		# i realise this might not be the first monday and tuesday but doesn't matter for this test
		first_monday = add_days(first_sunday, 1)
		first_tuesday = add_days(first_monday, 1)
		second_sunday = add_days(first_sunday, 7)
		second_tuesday = add_days(first_tuesday, 7)

		# employees working on holidays
		mark_attendance(emp1, first_sunday, "Present")
		mark_attendance(emp1, second_sunday, "Present")
		mark_attendance(emp2, first_monday, "Present")
		mark_attendance(emp3, second_tuesday, "Present")

		# employees working on working days
		mark_attendance(emp1, first_tuesday, "Present")
		mark_attendance(emp2, first_sunday, "Present")
		mark_attendance(emp3, first_monday, "Present")

		filters = frappe._dict(
			{
				"from_date": from_date,
				"to_date": to_date,
				"company": self.company,
			}
		)
		report = execute(filters=filters)
		rows = report[1]

		self.assertEqual(len(rows), 4)

		weekly_offs = {
			emp1: "Sunday",
			emp2: "Monday",
			emp3: "Tuesday",
		}

		for d in rows:
			self.assertEqual(weekly_offs[d[0]], d[4])

	def test_report_uses_business_date_holiday_list(self):
		employee = make_employee("test_holiday_report_hla_as_on@example.com", company=self.company)
		holiday_list_a = make_holiday_list(
			"Test Holiday Report HLA A",
			from_date="2026-01-01",
			to_date="2026-01-31",
			add_weekly_offs=False,
		)
		holiday_list_b = make_holiday_list(
			"Test Holiday Report HLA B",
			from_date="2026-01-01",
			to_date="2026-12-31",
			add_weekly_offs=False,
		)
		add_date_to_holiday_list("2026-01-01", holiday_list_a)
		add_date_to_holiday_list("2026-01-02", holiday_list_b)
		create_holiday_list_assignment(
			"Employee", assigned_to=employee, holiday_list=holiday_list_a, from_date="2026-01-01"
		)
		create_holiday_list_assignment(
			"Employee", assigned_to=employee, holiday_list=holiday_list_b, from_date="2026-06-01"
		)
		mark_attendance(employee, "2026-01-01", "Present")

		report = execute(
			filters=frappe._dict(
				{
					"from_date": "2026-01-01",
					"to_date": "2026-01-31",
					"company": self.company,
				}
			)
		)
		employee_rows = [row for row in report[1] if row[0] == employee]

		self.assertEqual(len(employee_rows), 1)
		self.assertEqual(employee_rows[0][2], getdate("2026-01-01"))
