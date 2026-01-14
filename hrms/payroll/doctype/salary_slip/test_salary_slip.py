# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import calendar
import random

import frappe
from frappe.core.doctype.user_permission.test_user_permission import create_user
from frappe.model.document import Document
from frappe.tests import IntegrationTestCase, change_settings
from frappe.utils import (
	add_days,
	add_months,
	cstr,
	date_diff,
	flt,
	get_first_day,
	get_last_day,
	get_year_ending,
	get_year_start,
	getdate,
	nowdate,
	rounded,
)
from frappe.utils.make_random import get_random

import erpnext
from erpnext.accounts.utils import get_fiscal_year
from erpnext.setup.doctype.employee.employee import InactiveEmployeeStatusError
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.leave_allocation.test_leave_allocation import create_leave_allocation
from hrms.hr.doctype.leave_type.test_leave_type import create_leave_type
from hrms.payroll.doctype.employee_tax_exemption_declaration.test_employee_tax_exemption_declaration import (
	create_exemption_category,
	create_payroll_period,
)
from hrms.payroll.doctype.payroll_entry.payroll_entry import get_month_details
from hrms.payroll.doctype.salary_slip.salary_slip import (
	HOLIDAYS_BETWEEN_DATES,
	LEAVE_TYPE_MAP,
	SALARY_COMPONENT_VALUES,
	TAX_COMPONENTS_BY_COMPANY,
	SalarySlip,
	_safe_eval,
	make_salary_slip_from_timesheet,
)
from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
from hrms.tests.test_utils import get_email_by_subject, get_first_sunday


class TestSalarySlip(IntegrationTestCase):
	def setUp(self):
		setup_test()
		frappe.flags.pop("via_payroll_entry", None)
		create_ss_email_template()
		clear_cache()

	def tearDown(self):
		frappe.db.set_single_value("Payroll Settings", "include_holidays_in_total_working_days", 0)
		frappe.set_user("Administrator")
		clear_cache()

	@change_settings("Payroll Settings", {"show_leave_balances_in_salary_slip": True})
	def test_leave_details(self):
		from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure

		emp_id = make_employee("test_leave_details@salary.com")

		first_sunday = get_first_sunday()
		alloc = create_leave_allocation(
			employee=emp_id,
			from_date=first_sunday,
			to_date=add_months(first_sunday, 10),
			new_leaves_allocated=10,
			leave_type="_Test Leave Type",
		)
		alloc.save()
		alloc.submit()

		make_leave_application(emp_id, first_sunday, add_days(first_sunday, 3), "_Test Leave Type")
		next_month = add_months(nowdate(), 1)
		make_leave_application(emp_id, next_month, add_days(next_month, 3), "_Test Leave Type")
		ss = make_employee_salary_slip(emp_id, "Monthly")

		leave_detail = ss.leave_details[0]
		self.assertEqual(leave_detail.leave_type, "_Test Leave Type")
		self.assertEqual(leave_detail.total_allocated_leaves, 10)
		self.assertEqual(leave_detail.expired_leaves, 0)
		self.assertEqual(leave_detail.used_leaves, 4)
		self.assertEqual(leave_detail.available_leaves, 6)

	def test_employee_status_inactive(self):
		from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure

		employee = make_employee("test_employee_status@company.com")
		employee_doc = frappe.get_doc("Employee", employee)
		employee_doc.status = "Inactive"
		employee_doc.save()
		employee_doc.reload()

		make_holiday_list()
		frappe.db.set_value(
			"Company", employee_doc.company, "default_holiday_list", "Salary Slip Test Holiday List"
		)

		frappe.db.sql("""delete from `tabSalary Structure` where name='Test Inactive Employee Salary Slip'""")
		salary_structure = make_salary_structure(
			"Test Inactive Employee Salary Slip",
			"Monthly",
			employee=employee_doc.name,
			company=employee_doc.company,
		)
		salary_slip = make_salary_slip(salary_structure.name, employee=employee_doc.name)

		self.assertRaises(InactiveEmployeeStatusError, salary_slip.save)

	@change_settings(
		"Payroll Settings", {"payroll_based_on": "Attendance", "daily_wages_fraction_for_half_day": 0.75}
	)
	def test_payment_days_based_on_attendance(self):
		no_of_days = get_no_of_days()

		emp_id = make_employee("test_payment_days_based_on_attendance@salary.com")
		frappe.db.set_value("Employee", emp_id, {"relieving_date": None, "status": "Active"})

		frappe.db.set_value("Leave Type", "Leave Without Pay", "include_holiday", 0)

		first_sunday = get_first_sunday()

		mark_attendance(emp_id, first_sunday, "Absent", ignore_validate=True)  # invalid lwp
		mark_attendance(
			emp_id, add_days(first_sunday, 1), "Absent", ignore_validate=True
		)  # counted as absent
		mark_attendance(
			emp_id,
			add_days(first_sunday, 2),
			"Half Day",
			leave_type="Leave Without Pay",
			ignore_validate=True,
			half_day_status="Present",
		)  # valid 0.75 lwp
		mark_attendance(
			emp_id,
			add_days(first_sunday, 3),
			"On Leave",
			leave_type="Leave Without Pay",
			ignore_validate=True,
		)  # valid lwp
		mark_attendance(
			emp_id, add_days(first_sunday, 4), "On Leave", leave_type="Casual Leave", ignore_validate=True
		)  # invalid lwp
		mark_attendance(
			emp_id,
			add_days(first_sunday, 7),
			"On Leave",
			leave_type="Leave Without Pay",
			ignore_validate=True,
		)  # invalid lwp

		ss = make_employee_salary_slip(
			emp_id,
			"Monthly",
			"Test Payment Based On Attendence",
		)

		self.assertEqual(ss.leave_without_pay, 1.25)
		self.assertEqual(ss.absent_days, 1)

		days_in_month = no_of_days[0]
		no_of_holidays = no_of_days[1]

		self.assertEqual(ss.payment_days, days_in_month - no_of_holidays - 2.25)

		# Gross pay calculation based on attendances
		gross_pay = 78000 - (
			(78000 / (days_in_month - no_of_holidays)) * flt(ss.leave_without_pay + ss.absent_days)
		)

		self.assertEqual(rounded(ss.gross_pay), rounded(gross_pay))

	@change_settings(
		"Payroll Settings",
		{
			"payroll_based_on": "Attendance",
			"consider_unmarked_attendance_as": "Absent",
			"daily_wages_fraction_for_half_day": 0.5,
		},
	)
	def test_payment_days_considering_half_days_unmarked_as_absent(self):
		no_of_days = get_no_of_days()

		emp_id = make_employee("test_payment_days_based_on_attendance1@salary.com")

		first_sunday = get_first_sunday()
		mark_attendance(
			emp_id, add_days(first_sunday, 1), "Present", ignore_validate=True
		)  # counted as Present
		mark_attendance(
			emp_id,
			add_days(first_sunday, 2),
			"Half Day",
			leave_type="Casual Leave",
			ignore_validate=True,
			half_day_status="Absent",
		)  # count as half absent in absent days
		mark_attendance(
			emp_id, add_days(first_sunday, 3), "Half Day", ignore_validate=True, half_day_status="Absent"
		)  # count as half absent in absent days
		mark_attendance(
			emp_id, add_days(first_sunday, 4), "Half Day", ignore_validate=True, half_day_status="Present"
		)  # count as full present
		mark_attendance(
			emp_id, add_days(first_sunday, 5), "On Leave", leave_type="Casual Leave", ignore_validate=True
		)  # invalid lwp, full present
		mark_attendance(
			emp_id,
			add_days(first_sunday, 6),
			"Half Day",
			leave_type="Leave Without Pay",
			ignore_validate=True,
			half_day_status="Absent",
		)  # count as 0.5 lwp and 0.5 in absent days

		ss = make_employee_salary_slip(
			emp_id,
			"Monthly",
			"Test Payment Based On Attendence",
		)
		days_in_month = no_of_days[0]
		no_of_holidays = no_of_days[1]
		# from half lwp
		self.assertEqual(ss.leave_without_pay, 0.5)
		# 1 + 0.5 + 0.5 + 1 + 1 + 0.5
		self.assertEqual(ss.absent_days, (days_in_month - no_of_holidays - 4.5))

		self.assertEqual(ss.payment_days, 4)

		# Gross pay calculation based on attendances
		gross_pay = 78000 - (
			(78000 / (days_in_month - no_of_holidays)) * flt(ss.leave_without_pay + ss.absent_days)
		)
		# half day (when absent) from checkins is considered as 0.5 lwp but half day (absent) from leave application is considered as absent
		self.assertEqual(rounded(ss.gross_pay), rounded(gross_pay))

	@change_settings(
		"Payroll Settings",
		{
			"payroll_based_on": "Attendance",
			"consider_unmarked_attendance_as": "Present",
			"daily_wages_fraction_for_half_day": 0.5,
		},
	)
	def test_payment_days_considering_half_days_unmarked_as_present(self):
		no_of_days = get_no_of_days()

		emp_id = make_employee("test_payment_days_based_on_attendance2@salary.com")

		first_sunday = get_first_sunday()
		mark_attendance(
			emp_id, add_days(first_sunday, 1), "Absent", ignore_validate=True
		)  # counted as absent
		mark_attendance(
			emp_id,
			add_days(first_sunday, 2),
			"Half Day",
			leave_type="Casual Leave",
			ignore_validate=True,
			half_day_status="Absent",
		)  # count as full present
		mark_attendance(
			emp_id, add_days(first_sunday, 3), "Half Day", ignore_validate=True, half_day_status="Absent"
		)  # count as full present
		mark_attendance(
			emp_id, add_days(first_sunday, 4), "Half Day", ignore_validate=True, half_day_status="Present"
		)  # count as full present
		mark_attendance(
			emp_id, add_days(first_sunday, 5), "On Leave", leave_type="Casual Leave", ignore_validate=True
		)  # invalid lwp, full present
		mark_attendance(
			emp_id,
			add_days(first_sunday, 6),
			"Half Day",
			leave_type="Leave Without Pay",
			ignore_validate=True,
			half_day_status="Absent",
		)  # count as 0.5 lwp and 0.5 as present

		ss = make_employee_salary_slip(
			emp_id,
			"Monthly",
			"Test Payment Based On Attendence",
		)
		days_in_month = no_of_days[0]
		no_of_holidays = no_of_days[1]
		# from half lwp
		self.assertEqual(ss.leave_without_pay, 0.5)

		self.assertEqual(ss.absent_days, 2.5)

		# total payment days = total working days - lwp - absent days
		self.assertEqual(ss.payment_days, days_in_month - no_of_holidays - 0.5 - 2.5)

		# Gross pay calculation based on attendances
		gross_pay = 78000 - (
			(78000 / (days_in_month - no_of_holidays)) * flt(ss.leave_without_pay + ss.absent_days)
		)
		# half day (when absent) from checkins is considered as 0.5 lwp but half day (absent) from leave application is considered as absent
		self.assertEqual(rounded(ss.gross_pay), rounded(gross_pay))

	@change_settings(
		"Payroll Settings",
		{
			"payroll_based_on": "Attendance",
			"consider_unmarked_attendance_as": "Absent",
			"include_holidays_in_total_working_days": True,
		},
	)
	def test_payment_days_for_mid_joinee_including_holidays(self):
		no_of_days = get_no_of_days()
		month_start_date, month_end_date = get_first_day(nowdate()), get_last_day(nowdate())

		new_emp_id = make_employee("test_payment_days_based_on_joining_date@salary.com")
		joining_date, relieving_date = add_days(month_start_date, 3), add_days(month_end_date, -5)

		for days in range(date_diff(month_end_date, month_start_date) + 1):
			date = add_days(month_start_date, days)
			mark_attendance(new_emp_id, date, "Present", ignore_validate=True)

		# Case 1: relieving in mid month
		frappe.db.set_value(
			"Employee",
			new_emp_id,
			{"date_of_joining": month_start_date, "relieving_date": relieving_date, "status": "Active"},
		)

		new_ss = make_employee_salary_slip(
			new_emp_id,
			"Monthly",
			"Test Payment Based On Attendence",
		)
		self.assertEqual(new_ss.payment_days, no_of_days[0] - 5)

		# Case 2: joining in mid month
		frappe.db.set_value(
			"Employee",
			new_emp_id,
			{"date_of_joining": joining_date, "relieving_date": month_end_date, "status": "Active"},
		)

		frappe.delete_doc("Salary Slip", new_ss.name, force=True)
		new_ss = make_employee_salary_slip(
			new_emp_id,
			"Monthly",
			"Test Payment Based On Attendence",
		)
		self.assertEqual(new_ss.payment_days, no_of_days[0] - 3)

		# Case 3: joining and relieving in mid-month
		frappe.db.set_value(
			"Employee",
			new_emp_id,
			{"date_of_joining": joining_date, "relieving_date": relieving_date, "status": "Left"},
		)

		frappe.delete_doc("Salary Slip", new_ss.name, force=True)
		new_ss = make_employee_salary_slip(
			new_emp_id,
			"Monthly",
			"Test Payment Based On Attendence",
		)

		self.assertEqual(new_ss.total_working_days, no_of_days[0])
		self.assertEqual(new_ss.payment_days, no_of_days[0] - 8)

	@change_settings(
		"Payroll Settings",
		{
			"payroll_based_on": "Attendance",
			"consider_unmarked_attendance_as": "Absent",
			"include_holidays_in_total_working_days": True,
		},
	)
	def test_payment_days_for_mid_joinee_including_holidays_and_unmarked_days(self):
		# tests mid month joining and relieving along with unmarked days
		from erpnext.setup.doctype.holiday_list.holiday_list import is_holiday

		no_of_days = get_no_of_days()
		month_start_date, month_end_date = get_first_day(nowdate()), get_last_day(nowdate())

		new_emp_id = make_employee("test_payment_days_based_on_joining_date@salary.com")
		joining_date, relieving_date = add_days(month_start_date, 3), add_days(month_end_date, -5)

		for days in range(date_diff(relieving_date, joining_date) + 1):
			date = add_days(joining_date, days)
			if not is_holiday("Salary Slip Test Holiday List", date):
				mark_attendance(new_emp_id, date, "Present", ignore_validate=True)

		frappe.db.set_value(
			"Employee",
			new_emp_id,
			{"date_of_joining": joining_date, "relieving_date": relieving_date, "status": "Left"},
		)

		new_ss = make_employee_salary_slip(
			new_emp_id,
			"Monthly",
			"Test Payment Based On Attendence",
		)

		self.assertEqual(new_ss.total_working_days, no_of_days[0])
		self.assertEqual(new_ss.payment_days, no_of_days[0] - 8)

	@change_settings(
		"Payroll Settings",
		{
			"payroll_based_on": "Attendance",
			"consider_unmarked_attendance_as": "Absent",
			"include_holidays_in_total_working_days": False,
		},
	)
	def test_payment_days_for_mid_joinee_excluding_holidays(self):
		from erpnext.setup.doctype.holiday_list.holiday_list import is_holiday

		no_of_days = get_no_of_days()
		month_start_date, month_end_date = get_first_day(nowdate()), get_last_day(nowdate())

		new_emp_id = make_employee("test_payment_days_based_on_joining_date@salary.com")
		joining_date, relieving_date = add_days(month_start_date, 3), add_days(month_end_date, -5)
		frappe.db.set_value(
			"Employee",
			new_emp_id,
			{"date_of_joining": joining_date, "relieving_date": relieving_date, "status": "Left"},
		)

		holidays = 0

		for days in range(date_diff(relieving_date, joining_date) + 1):
			date = add_days(joining_date, days)
			if not is_holiday("Salary Slip Test Holiday List", date):
				mark_attendance(new_emp_id, date, "Present", ignore_validate=True)
			else:
				holidays += 1

		new_ss = make_employee_salary_slip(
			new_emp_id,
			"Monthly",
			"Test Payment Based On Attendence",
		)

		self.assertEqual(new_ss.total_working_days, no_of_days[0] - no_of_days[1])
		self.assertEqual(new_ss.payment_days, no_of_days[0] - holidays - 8)

	@change_settings("Payroll Settings", {"payroll_based_on": "Leave"})
	def test_payment_days_based_on_leave_application(self):
		no_of_days = get_no_of_days()

		emp_id = make_employee("test_payment_days_based_on_leave_application@salary.com")
		frappe.db.set_value("Employee", emp_id, {"relieving_date": None, "status": "Active"})

		frappe.db.set_value("Leave Type", "Leave Without Pay", "include_holiday", 0)

		first_sunday = get_first_sunday()

		# 3 days LWP
		make_leave_application(emp_id, first_sunday, add_days(first_sunday, 3), "Leave Without Pay")

		create_leave_type(leave_type_name="Test Partially Paid Leave", is_ppl=1)

		alloc = create_leave_allocation(
			employee=emp_id,
			from_date=add_days(first_sunday, 4),
			to_date=add_days(first_sunday, 10),
			new_leaves_allocated=3,
			leave_type="Test Partially Paid Leave",
		)
		alloc.save()
		alloc.submit()

		# 1.5 day leave ppl with fraction_of_daily_salary_per_leave = 0.5 equivalent to single day lwp = 0.75
		make_leave_application(
			emp_id,
			add_days(first_sunday, 4),
			add_days(first_sunday, 5),
			"Test Partially Paid Leave",
			half_day=True,
			half_day_date=add_days(first_sunday, 4),
		)

		ss = make_employee_salary_slip(
			emp_id,
			"Monthly",
			"Test Payment Based On Leave Application",
		)

		self.assertEqual(ss.leave_without_pay, 3.75)

		days_in_month = no_of_days[0]
		no_of_holidays = no_of_days[1]

		self.assertEqual(ss.payment_days, days_in_month - no_of_holidays - 3.75)

	@change_settings("Payroll Settings", {"payroll_based_on": "Leave"})
	def test_payment_days_calculation_for_lwp_on_month_boundaries(self):
		from hrms.hr.doctype.holiday_list_assignment.test_holiday_list_assignment import (
			create_holiday_list_assignment,
		)

		"""Tests LWP calculation leave applications created on month boundaries"""
		holiday_list = make_holiday_list(
			"Test Holiday List",
			"2024-01-01",
			"2024-12-31",
		)
		emp_id = make_employee(
			"test_payment_days_based_on_leave_application@salary.com", holiday_list=holiday_list
		)
		create_holiday_list_assignment("Employee", emp_id, holiday_list)
		make_leave_application(emp_id, "2024-06-28", "2024-07-03", "Leave Without Pay")  # 3 days in July
		make_leave_application(emp_id, "2024-07-10", "2024-07-13", "Leave Without Pay")  # 4 days in July
		make_leave_application(emp_id, "2024-07-28", "2024-08-05", "Leave Without Pay")  # 3 days in July

		ss = make_employee_salary_slip(
			emp_id, "Monthly", "Test Payment Based On Leave Application", "2024-07-01"
		)

		self.assertEqual(ss.leave_without_pay, 10)
		self.assertEqual(ss.payment_days, 17)

	@change_settings("Payroll Settings", {"payroll_based_on": "Attendance"})
	def test_payment_days_in_salary_slip_based_on_timesheet(self):
		from erpnext.projects.doctype.timesheet.test_timesheet import make_timesheet

		emp = make_employee(
			"test_employee_timesheet@salary.com",
			company="_Test Company",
			holiday_list="Salary Slip Test Holiday List",
		)
		frappe.db.set_value("Employee", emp, {"relieving_date": None, "status": "Active"})

		# mark attendance
		first_sunday = get_first_sunday()

		mark_attendance(emp, add_days(first_sunday, 1), "Absent", ignore_validate=True)  # counted as absent

		# salary structure based on timesheet
		make_salary_structure_for_timesheet(emp)
		timesheet = make_timesheet(emp, simulate=True, is_billable=1)
		salary_slip = make_salary_slip_from_timesheet(timesheet.name)
		salary_slip.start_date = get_first_day(nowdate())
		salary_slip.end_date = get_last_day(nowdate())
		salary_slip.save()
		salary_slip.submit()
		salary_slip.reload()

		no_of_days = get_no_of_days()
		days_in_month = no_of_days[0]
		no_of_holidays = no_of_days[1]

		self.assertEqual(salary_slip.payment_days, days_in_month - no_of_holidays - 1)

		# component calculation based on attendance (payment days)
		amount, precision = None, None

		for row in salary_slip.earnings:
			if row.salary_component == "Basic Salary":
				amount = row.amount
				precision = row.precision("amount")
				break
		expected_amount = flt((50000 * salary_slip.payment_days / salary_slip.total_working_days), precision)

		self.assertEqual(amount, expected_amount)

	@change_settings("Payroll Settings", {"payroll_based_on": "Attendance"})
	def test_component_amount_dependent_on_another_payment_days_based_component(self):
		from hrms.payroll.doctype.salary_structure.test_salary_structure import (
			create_salary_structure_assignment,
		)

		salary_structure = make_salary_structure_for_payment_days_based_component_dependency()
		employee = make_employee("test_payment_days_based_component@salary.com", company="_Test Company")

		# base = 50000
		create_salary_structure_assignment(
			employee, salary_structure.name, company="_Test Company", currency="INR"
		)

		# mark employee absent for a day since this case works fine if payment days are equal to working days
		first_sunday = get_first_sunday()

		mark_attendance(
			employee, add_days(first_sunday, 1), "Absent", ignore_validate=True
		)  # counted as absent

		# make salary slip and assert payment days
		ss = make_salary_slip_for_payment_days_dependency_test(
			"test_payment_days_based_component@salary.com", salary_structure.name
		)
		self.assertEqual(ss.absent_days, 1)

		ss.reload()
		payment_days_based_comp_amount = 0
		for component in ss.earnings:
			if component.salary_component == "HRA - Payment Days":
				payment_days_based_comp_amount = flt(component.amount, component.precision("amount"))
				break

		# check if the dependent component is calculated using the amount updated after payment days
		actual_amount = 0
		precision = 0
		for component in ss.deductions:
			if component.salary_component == "P - Employee Provident Fund":
				precision = component.precision("amount")
				actual_amount = flt(component.amount, precision)
				break

		expected_amount = flt((flt(ss.gross_pay) - payment_days_based_comp_amount) * 0.12, precision)

		self.assertEqual(actual_amount, expected_amount)

	@change_settings("Payroll Settings", {"include_holidays_in_total_working_days": 1})
	def test_salary_slip_with_holidays_included(self):
		no_of_days = get_no_of_days()
		emp_id = make_employee(
			"test_salary_slip_with_holidays_included@salary.com",
			relieving_date=None,
			status="Active",
		)

		ss = make_employee_salary_slip(
			emp_id,
			"Monthly",
			"Test Salary Slip With Holidays Included",
		)

		self.assertEqual(ss.total_working_days, no_of_days[0])
		self.assertEqual(ss.payment_days, no_of_days[0])
		self.assertEqual(ss.earnings[0].amount, 50000)
		self.assertEqual(ss.earnings[1].amount, 3000)
		self.assertEqual(ss.gross_pay, 78000)

	@change_settings("Payroll Settings", {"include_holidays_in_total_working_days": 0})
	def test_salary_slip_with_holidays_excluded(self):
		no_of_days = get_no_of_days()
		emp_id = make_employee(
			"test_salary_slip_with_holidays_excluded@salary.com",
			relieving_date=None,
			status="Active",
		)

		ss = make_employee_salary_slip(
			emp_id,
			"Monthly",
			"Test Salary Slip With Holidays Excluded",
		)

		self.assertEqual(ss.total_working_days, no_of_days[0] - no_of_days[1])
		self.assertEqual(ss.payment_days, no_of_days[0] - no_of_days[1])
		self.assertEqual(ss.earnings[0].amount, 50000)
		self.assertEqual(ss.earnings[0].default_amount, 50000)
		self.assertEqual(ss.earnings[1].amount, 3000)
		self.assertEqual(ss.gross_pay, 78000)

	@change_settings(
		"Payroll Settings",
		{
			"payroll_based_on": "Attendance",
			"consider_unmarked_attendance_as": "Present",
			"include_holidays_in_total_working_days": 1,
			"consider_marked_attendance_on_holidays": 1,
		},
	)
	def test_consider_marked_attendance_on_holidays(self):
		no_of_days = get_no_of_days()
		emp_id = make_employee(
			"test_salary_slip_with_holidays_included@salary.com",
			relieving_date=None,
			status="Active",
		)

		# mark absent on holiday
		first_sunday = get_first_sunday(for_date=getdate())
		mark_attendance(emp_id, first_sunday, "Absent", ignore_validate=True)

		ss = make_employee_salary_slip(
			emp_id,
			"Monthly",
			"Test Salary Slip With Holidays Included",
		)

		self.assertEqual(ss.total_working_days, no_of_days[0])
		# deduct 1 day for absent on holiday
		self.assertEqual(ss.payment_days, no_of_days[0] - 1)

		# disable consider marked attendance on holidays
		frappe.db.set_single_value("Payroll Settings", "consider_marked_attendance_on_holidays", 0)
		ss.save()
		self.assertEqual(ss.total_working_days, no_of_days[0])

	@change_settings(
		"Payroll Settings",
		{
			"payroll_based_on": "Attendance",
			"consider_unmarked_attendance_as": "Absent",
			"include_holidays_in_total_working_days": 1,
			"consider_marked_attendance_on_holidays": 1,
		},
	)
	def test_consider_marked_attendance_on_holidays_with_unmarked_attendance(self):
		from erpnext.setup.doctype.holiday_list.holiday_list import is_holiday

		no_of_days = get_no_of_days()
		month_start_date, month_end_date = get_first_day(nowdate()), get_last_day(nowdate())
		joining_date = add_days(month_start_date, 3)

		emp_id = make_employee(
			"test_salary_slip_with_holidays_included1@salary.com",
			status="Active",
			date_of_joining=joining_date,
			relieving_date=None,
		)

		for days in range(date_diff(month_end_date, joining_date) + 1):
			date = add_days(joining_date, days)
			if not is_holiday("Salary Slip Test Holiday List", date):
				mark_attendance(emp_id, date, "Present", ignore_validate=True)

		# mark absent on holiday
		first_sunday = get_first_sunday(for_date=joining_date, find_after_for_date=True)
		mark_attendance(emp_id, first_sunday, "Absent", ignore_validate=True)

		# unmarked attendance for a day
		frappe.db.delete("Attendance", {"employee": emp_id, "attendance_date": add_days(first_sunday, 1)})

		ss = make_employee_salary_slip(
			emp_id,
			"Monthly",
			"Test Salary Slip With Holidays Included",
		)

		self.assertEqual(ss.total_working_days, no_of_days[0])
		# no_of_days - absent on holiday - period before DOJ - 1 unmarked attendance
		self.assertEqual(ss.payment_days, no_of_days[0] - 1 - 3 - 1)

		# disable consider marked attendance on holidays
		frappe.db.set_single_value("Payroll Settings", "consider_marked_attendance_on_holidays", 0)
		ss.save()
		self.assertEqual(ss.total_working_days, no_of_days[0])
		# no_of_days - period before DOJ
		self.assertEqual(ss.payment_days, no_of_days[0] - 3 - 1)

	@change_settings(
		"Payroll Settings",
		{
			"payroll_based_on": "Attendance",
			"consider_unmarked_attendance_as": "Present",
			"include_holidays_in_total_working_days": 1,
			"consider_marked_attendance_on_holidays": 0,
		},
	)
	def test_consider_marked_attendance_on_holidays_with_half_day_on_holiday(self):
		from erpnext.setup.doctype.holiday_list.holiday_list import is_holiday

		no_of_days = get_no_of_days()
		month_start_date, month_end_date = get_first_day(nowdate()), get_last_day(nowdate())
		joining_date = add_days(month_start_date, 3)

		emp_id = make_employee(
			"test_salary_slip_with_holidays_included1@salary.com",
			status="Active",
			date_of_joining=joining_date,
			relieving_date=None,
		)

		for days in range(date_diff(month_end_date, joining_date) + 1):
			date = add_days(joining_date, days)
			if not is_holiday("Salary Slip Test Holiday List", date):
				mark_attendance(emp_id, date, "Present", ignore_validate=True)

		# mark half day on holiday
		first_sunday = get_first_sunday(for_date=joining_date, find_after_for_date=True)
		mark_attendance(
			emp_id,
			first_sunday,
			"Half Day",
			half_day_status="Absent",
			ignore_validate=True,
		)

		ss = make_employee_salary_slip(
			emp_id,
			"Monthly",
			"Test Salary Slip With Holidays Included",
		)

		self.assertEqual(ss.total_working_days, no_of_days[0])
		# no_of_days - period before DOJ
		self.assertEqual(ss.payment_days, no_of_days[0] - 3)

		# enable consider marked attendance on holidays
		frappe.db.set_single_value("Payroll Settings", "consider_marked_attendance_on_holidays", 1)
		ss.save()
		self.assertEqual(ss.total_working_days, no_of_days[0])
		# no_of_days - period before DOJ - 0.5 LWP on holiday (half day present)
		self.assertEqual(ss.payment_days, no_of_days[0] - 3 - 0.5)

	@change_settings("Payroll Settings", {"include_holidays_in_total_working_days": 1})
	def test_payment_days(self):
		from hrms.payroll.doctype.salary_structure.test_salary_structure import (
			create_salary_structure_assignment,
		)

		no_of_days = get_no_of_days()

		# set joinng date in the same month
		emp_id = make_employee("test_payment_days@salary.com")
		if getdate(nowdate()).day >= 15:
			relieving_date = getdate(add_days(nowdate(), -10))
			date_of_joining = getdate(add_days(nowdate(), -10))
		elif getdate(nowdate()).day < 15 and getdate(nowdate()).day >= 5:
			date_of_joining = getdate(add_days(nowdate(), -3))
			relieving_date = getdate(add_days(nowdate(), -3))
		elif getdate(nowdate()).day < 5 and not getdate(nowdate()).day == 1:
			date_of_joining = getdate(add_days(nowdate(), -1))
			relieving_date = getdate(add_days(nowdate(), -1))
		elif getdate(nowdate()).day == 1:
			date_of_joining = getdate(nowdate())
			relieving_date = getdate(nowdate())

		frappe.db.set_value(
			"Employee",
			emp_id,
			{"date_of_joining": date_of_joining, "relieving_date": None, "status": "Active"},
		)

		salary_structure = "Test Payment Days"
		ss = make_employee_salary_slip(emp_id, "Monthly", salary_structure)

		self.assertEqual(ss.total_working_days, no_of_days[0])
		self.assertEqual(ss.payment_days, (no_of_days[0] - getdate(date_of_joining).day + 1))

		# set relieving date in the same month
		frappe.db.set_value(
			"Employee",
			emp_id,
			{
				"date_of_joining": add_days(nowdate(), -60),
				"relieving_date": relieving_date,
				"status": "Left",
			},
		)

		if date_of_joining.day > 1:
			self.assertRaises(frappe.ValidationError, ss.save)

		create_salary_structure_assignment(emp_id, salary_structure)
		ss.reload()
		ss.save()

		self.assertEqual(ss.total_working_days, no_of_days[0])
		self.assertEqual(ss.payment_days, getdate(relieving_date).day)

		frappe.db.set_value(
			"Employee",
			emp_id,
			{
				"relieving_date": None,
				"status": "Active",
			},
		)

	def test_employee_salary_slip_read_permission(self):
		emp_id = make_employee("test_employee_salary_slip_read_permission@salary.com")

		salary_slip_test_employee = make_employee_salary_slip(
			emp_id,
			"Monthly",
			"Test Employee Salary Slip Read Permission",
		)
		frappe.set_user("test_employee_salary_slip_read_permission@salary.com")
		self.assertTrue(salary_slip_test_employee.has_permission("read"))

	@change_settings("Payroll Settings", {"email_salary_slip_to_employee": 1})
	def test_email_salary_slip(self):
		frappe.db.delete("Email Queue")

		emp_id = make_employee("test_email_salary_slip@salary.com", company="_Test Company")
		ss = make_employee_salary_slip(emp_id, "Monthly", "Test Salary Slip Email")
		ss.company = "_Test Company"
		ss.save()
		ss.submit()

		self.assertIsNotNone(get_email_by_subject("Salary Slip - from"))

	@change_settings(
		"Payroll Settings", {"email_salary_slip_to_employee": 1, "email_template": "Salary Slip"}
	)
	def test_email_salary_slip_with_email_template(self):
		frappe.db.delete("Email Queue")

		emp_id = make_employee("test_email_salary_slip@salary.com", company="_Test Company")
		ss = make_employee_salary_slip(emp_id, "Monthly", "Test Salary Slip Email")
		ss.company = "_Test Company"
		ss.save()
		ss.submit()

		self.assertIsNotNone(get_email_by_subject("Test Salary Slip Email Template"))

	def test_payroll_frequency(self):
		fiscal_year = get_fiscal_year(nowdate(), company=erpnext.get_default_company())[0]
		month = "%02d" % getdate(nowdate()).month
		m = get_month_details(fiscal_year, month)

		for payroll_frequency in ["Monthly", "Bimonthly", "Fortnightly", "Weekly", "Daily"]:
			emp_id = make_employee(payroll_frequency + "_test_employee@salary.com")
			ss = make_employee_salary_slip(
				emp_id,
				payroll_frequency,
				payroll_frequency + "_Test Payroll Frequency",
			)
			if payroll_frequency == "Monthly":
				self.assertEqual(ss.end_date, m["month_end_date"])
			elif payroll_frequency == "Bimonthly":
				if getdate(ss.start_date).day <= 15:
					self.assertEqual(ss.end_date, m["month_mid_end_date"])
				else:
					self.assertEqual(ss.end_date, m["month_end_date"])
			elif payroll_frequency == "Fortnightly":
				self.assertEqual(ss.end_date, add_days(nowdate(), 13))
			elif payroll_frequency == "Weekly":
				self.assertEqual(ss.end_date, add_days(nowdate(), 6))
			elif payroll_frequency == "Daily":
				self.assertEqual(ss.end_date, nowdate())

	def test_multi_currency_salary_slip(self):
		from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure

		applicant = make_employee("test_multi_currency_salary_slip@salary.com", company="_Test Company")
		frappe.db.sql("""delete from `tabSalary Structure` where name='Test Multi Currency Salary Slip'""")
		salary_structure = make_salary_structure(
			"Test Multi Currency Salary Slip",
			"Monthly",
			employee=applicant,
			company="_Test Company",
			currency="USD",
		)
		salary_slip = make_salary_slip(salary_structure.name, employee=applicant)
		salary_slip.exchange_rate = 70
		salary_slip.calculate_net_pay()

		self.assertEqual(salary_slip.gross_pay, 78000)
		self.assertEqual(salary_slip.base_gross_pay, 78000 * 70)

	def test_year_to_date_computation(self):
		from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure

		applicant = make_employee("test_ytd@salary.com", company="_Test Company")

		payroll_period = create_payroll_period(name="_Test Payroll Period", company="_Test Company")

		create_tax_slab(
			payroll_period,
			allow_tax_exemption=True,
			currency="INR",
			effective_date=getdate("2019-04-01"),
			company="_Test Company",
		)

		salary_structure = make_salary_structure(
			"Monthly Salary Structure Test for Salary Slip YTD",
			"Monthly",
			employee=applicant,
			company="_Test Company",
			currency="INR",
			payroll_period=payroll_period,
		)

		# clear salary slip for this employee
		frappe.db.sql("DELETE FROM `tabSalary Slip` where employee_name = 'test_ytd@salary.com'")

		create_salary_slips_for_payroll_period(
			applicant, salary_structure.name, payroll_period, deduct_random=False, num=6
		)

		salary_slips = frappe.get_all(
			"Salary Slip",
			fields=["year_to_date", "net_pay"],
			filters={"employee_name": "test_ytd@salary.com"},
			order_by="posting_date",
		)

		year_to_date = 0
		for slip in salary_slips:
			year_to_date += flt(slip.net_pay)
			self.assertEqual(slip.year_to_date, year_to_date)

	def test_component_wise_year_to_date_computation(self):
		from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure

		employee_name = "test_component_wise_ytd@salary.com"
		applicant = make_employee(employee_name, company="_Test Company")

		payroll_period = create_payroll_period(name="_Test Payroll Period", company="_Test Company")

		create_tax_slab(
			payroll_period,
			allow_tax_exemption=True,
			currency="INR",
			effective_date=getdate("2019-04-01"),
			company="_Test Company",
		)

		salary_structure = make_salary_structure(
			"Monthly Salary Structure Test for Salary Slip YTD",
			"Monthly",
			employee=applicant,
			company="_Test Company",
			currency="INR",
			payroll_period=payroll_period,
		)

		# clear salary slip for this employee
		frappe.db.sql("DELETE FROM `tabSalary Slip` where employee_name = '%s'" % employee_name)

		create_salary_slips_for_payroll_period(
			applicant, salary_structure.name, payroll_period, deduct_random=False, num=3
		)

		salary_slips = frappe.get_all(
			"Salary Slip",
			fields=["name"],
			filters={"employee_name": employee_name},
			order_by="posting_date",
		)

		year_to_date = dict()
		for slip in salary_slips:
			doc = frappe.get_doc("Salary Slip", slip.name)
			for entry in doc.get("earnings"):
				if not year_to_date.get(entry.salary_component):
					year_to_date[entry.salary_component] = 0

				year_to_date[entry.salary_component] += entry.amount
				self.assertEqual(year_to_date[entry.salary_component], entry.year_to_date)

	def test_tax_for_payroll_period(self):
		data = {}
		# test the impact of tax exemption declaration, tax exemption proof submission
		# and deduct check boxes in annual tax calculation
		# as per assigned salary structure 40500 in monthly salary so 236000*5/100/12
		frappe.db.sql("""delete from `tabPayroll Period`""")
		frappe.db.sql("""delete from `tabSalary Component`""")

		payroll_period = create_payroll_period()

		create_tax_slab(payroll_period, allow_tax_exemption=True)

		employee = make_employee("test_tax@salary.slip")
		delete_docs = [
			"Salary Slip",
			"Additional Salary",
			"Employee Tax Exemption Declaration",
			"Employee Tax Exemption Proof Submission",
			"Employee Benefit Claim",
			"Salary Structure Assignment",
		]
		for doc in delete_docs:
			frappe.db.sql(f"DELETE FROM `tab{doc}` WHERE employee='{employee}'")

		from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure

		salary_structure = make_salary_structure(
			"Structure to test tax",
			"Monthly",
			other_details={"max_benefits": 100000},
			test_tax=True,
			employee=employee,
			payroll_period=payroll_period,
		)

		# create salary slip for whole period deducting tax only on last period
		# to find the total tax amount paid
		create_salary_slips_for_payroll_period(
			employee, salary_structure.name, payroll_period, deduct_random=False
		)
		tax_paid = get_tax_paid_in_period(employee)

		annual_tax = 92789.0
		try:
			self.assertEqual(tax_paid, annual_tax)
		except AssertionError:
			print("\nSalary Slip - Annual tax calculation failed\n")
			raise
		frappe.db.sql("""delete from `tabSalary Slip` where employee=%s""", (employee))

		# create exemption declaration so the tax amount varies
		create_exemption_declaration(employee, payroll_period.name)

		# create for payroll deducting in random months
		data["deducted_dates"] = create_salary_slips_for_payroll_period(
			employee, salary_structure.name, payroll_period
		)
		tax_paid = get_tax_paid_in_period(employee)

		# No proof, total tax paid, should not change
		try:
			self.assertEqual(tax_paid, annual_tax)
		except AssertionError:
			print("\nSalary Slip - Tax calculation failed on following case\n", data, "\n")
			raise

		# Submit proof for total 120000
		data["proof"] = create_proof_submission(employee, payroll_period, 120000)

		frappe.db.sql("""delete from `tabSalary Slip` where employee=%s""", (employee))
		data["deducted_dates"] = create_salary_slips_for_payroll_period(
			employee, salary_structure.name, payroll_period
		)
		tax_paid = get_tax_paid_in_period(employee)

		# total taxable income 416000, 166000 @ 5% ie. 8300
		try:
			self.assertEqual(tax_paid, 71989.0)
		except AssertionError:
			print("\nSalary Slip - Tax calculation failed on following case\n", data, "\n")
			raise

		# create additional salary of 150000
		frappe.db.sql("""delete from `tabSalary Slip` where employee=%s""", (employee))
		data["additional-1"] = create_additional_salary(employee, payroll_period, 150000)
		data["deducted_dates"] = create_salary_slips_for_payroll_period(
			employee, salary_structure.name, payroll_period
		)

		annual_tax = 103189.0
		# total taxable income 566000, 250000 @ 5%, 66000 @ 20%, 12500 + 13200
		tax_paid = get_tax_paid_in_period(employee)
		try:
			self.assertEqual(tax_paid, annual_tax)
		except AssertionError:
			print("\nSalary Slip - Tax calculation failed on following case\n", data, "\n")
			raise
		frappe.db.sql("""delete from `tabAdditional Salary` where employee=%s""", (employee))

		# undelete fixture data
		frappe.db.rollback()

	@change_settings(
		"Payroll Settings",
		{
			"payroll_based_on": "Attendance",
			"consider_unmarked_attendance_as": "Present",
			"include_holidays_in_total_working_days": True,
		},
	)
	def test_default_amount(self):
		# Special Allowance (SA) uses another component Basic (BS) in it's formula : BD * .5
		# Basic has "Depends on Payment Days" enabled
		# Test default amount for SA is based on default amount for BS (irrespective of PD)
		# Test amount for SA is based on amount for BS (based on PD)
		from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure

		month_start_date = get_first_day(nowdate())
		joining_date = add_days(month_start_date, 3)
		employee = make_employee("test_tax_for_mid_joinee@salary.com", date_of_joining=joining_date)

		salary_structure = make_salary_structure(
			"Structure to test tax",
			"Monthly",
			test_tax=True,
			from_date=joining_date,
			employee=employee,
		)

		ss = make_salary_slip(salary_structure.name, employee=employee)

		# default amount for SA (special allowance = BS*0.5) should be based on default amount for basic
		self.assertEqual(ss.earnings[2].default_amount, 25000)
		self.assertEqual(
			ss.earnings[2].amount, flt(ss.earnings[0].amount * 0.5, ss.earnings[0].precision("amount"))
		)

	def test_tax_for_recurring_additional_salary(self):
		frappe.db.sql("""delete from `tabPayroll Period`""")
		frappe.db.sql("""delete from `tabSalary Component`""")

		payroll_period = create_payroll_period()

		create_tax_slab(payroll_period, allow_tax_exemption=True)

		employee = make_employee("test_tax@salary.slip")
		delete_docs = [
			"Salary Slip",
			"Additional Salary",
			"Employee Tax Exemption Declaration",
			"Employee Tax Exemption Proof Submission",
			"Employee Benefit Claim",
			"Salary Structure Assignment",
		]
		for doc in delete_docs:
			frappe.db.sql(f"DELETE FROM `tab{doc}` WHERE employee='{employee}'")

		from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure

		salary_structure = make_salary_structure(
			"Structure to test tax",
			"Monthly",
			other_details={"max_benefits": 100000},
			test_tax=True,
			employee=employee,
			payroll_period=payroll_period,
		)

		create_salary_slips_for_payroll_period(
			employee, salary_structure.name, payroll_period, deduct_random=False, num=3
		)

		tax_paid = get_tax_paid_in_period(employee)

		annual_tax = 23196.0
		self.assertEqual(tax_paid, annual_tax)

		frappe.db.sql("""delete from `tabSalary Slip` where employee=%s""", (employee))

		# ------------------------------------
		# Recurring additional salary
		start_date = add_months(payroll_period.start_date, 3)
		end_date = add_months(payroll_period.start_date, 5)
		create_recurring_additional_salary(employee, "Performance Bonus", 20000, start_date, end_date)

		frappe.db.sql("""delete from `tabSalary Slip` where employee=%s""", (employee))

		create_salary_slips_for_payroll_period(
			employee, salary_structure.name, payroll_period, deduct_random=False, num=4
		)

		tax_paid = get_tax_paid_in_period(employee)

		annual_tax = 32315.0
		self.assertEqual(tax_paid, annual_tax)

		frappe.db.rollback()

	def test_salary_slip_from_timesheet(self):
		from erpnext.projects.doctype.timesheet.test_timesheet import make_timesheet

		emp = make_employee("test_employee_6@salary.com", company="_Test Company")
		make_salary_structure_for_timesheet(emp)
		timesheet = make_timesheet(emp, simulate=True, is_billable=1)
		salary_slip = make_salary_slip_from_timesheet(timesheet.name)
		salary_slip.submit()

		self.assertEqual(salary_slip.total_working_hours, 2)
		self.assertEqual(salary_slip.hour_rate, 50)
		self.assertEqual(salary_slip.earnings[0].salary_component, "Timesheet Component")
		self.assertEqual(salary_slip.earnings[0].amount, 100)
		self.assertEqual(salary_slip.timesheets[0].time_sheet, timesheet.name)
		self.assertEqual(salary_slip.timesheets[0].working_hours, 2)

		timesheet = frappe.get_doc("Timesheet", timesheet.name)
		self.assertEqual(timesheet.status, "Payslip")
		salary_slip.cancel()

		timesheet = frappe.get_doc("Timesheet", timesheet.name)
		self.assertEqual(timesheet.status, "Submitted")

	def test_do_not_show_statistical_component_in_slip(self):
		emp_id = make_employee("test_statistical_component@salary.com")
		new_ss = make_employee_salary_slip(
			emp_id,
			"Monthly",
			"Test Payment Based On Attendence",
		)
		components = [row.salary_component for row in new_ss.get("earnings")]
		self.assertNotIn("Statistical Component", components)

	@change_settings(
		"Payroll Settings",
		{"payroll_based_on": "Attendance", "consider_unmarked_attendance_as": "Present"},
	)
	def test_statistical_component_based_on_payment_days(self):
		"""
		Tests whether component using statistical component in the formula
		gets the updated value based on payment days
		"""
		from hrms.payroll.doctype.salary_structure.test_salary_structure import (
			create_salary_structure_assignment,
		)

		emp = make_employee("test_statistical_component@salary.com")
		first_sunday = get_first_sunday()
		mark_attendance(emp, add_days(first_sunday, 1), "Absent", ignore_validate=True)
		salary_structure = make_salary_structure_for_payment_days_based_component_dependency(
			test_statistical_comp=True
		)
		create_salary_structure_assignment(
			emp, salary_structure.name, company="_Test Company", currency="INR"
		)
		# make salary slip and assert payment days
		ss = make_salary_slip_for_payment_days_dependency_test(
			"test_statistical_component@salary.com", salary_structure.name
		)

		amount = precision = None
		for entry in ss.earnings:
			if entry.salary_component == "Dependency Component":
				amount = entry.amount
				precision = entry.precision("amount")
				break

		self.assertEqual(
			amount, flt(flt((1000 * ss.payment_days / ss.total_working_days), precision) * 0.5, precision)
		)

	def make_activity_for_employee(self):
		activity_type = frappe.get_doc("Activity Type", "_Test Activity Type")
		activity_type.billing_rate = 50
		activity_type.costing_rate = 20
		activity_type.wage_rate = 25
		activity_type.save()

	def test_salary_slip_generation_against_opening_entries_in_ssa(self):
		import math

		from hrms.payroll.doctype.payroll_period.payroll_period import get_period_factor
		from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure

		frappe.db.sql("DELETE FROM `tabPayroll Period` where company = '_Test Company'")
		frappe.db.sql("DELETE FROM `tabIncome Tax Slab` where currency = 'INR'")

		payroll_period = create_payroll_period(
			name="_Test Payroll Period for Tax",
			company="_Test Company",
			start_date="2023-04-01",
			end_date="2024-03-31",
		)

		emp = make_employee(
			"test_employee_ss_with_opening_balance@salary.com",
			company="_Test Company",
			**{"date_of_joining": "2021-12-01"},
		)
		employee_doc = frappe.get_doc("Employee", emp)

		tax_slab = create_tax_slab(payroll_period, effective_date="2022-04-01", allow_tax_exemption=True)

		effective_date = frappe.db.get_value("Income Tax Slab", tax_slab, "effective_from")

		if effective_date != "2022-04-01":
			frappe.db.set_value("Income Tax Slab", tax_slab, "effective_from", "2022-04-01")

		salary_structure_name = "Test Salary Structure for Opening Balance"
		if not frappe.db.exists("Salary Structure", salary_structure_name):
			salary_structure_doc = make_salary_structure(
				salary_structure_name,
				"Monthly",
				company="_Test Company",
				employee=emp,
				from_date="2023-04-01",
				payroll_period=payroll_period,
				test_tax=True,
				currency="INR",
			)

		# validate no salary slip exists for the employee
		self.assertTrue(
			frappe.db.count(
				"Salary Slip",
				{
					"employee": emp,
					"salary_structure": salary_structure_doc.name,
					"docstatus": 1,
					"start_date": [">=", "2023-04-01"],
				},
			)
			== 0
		)

		remaining_sub_periods = get_period_factor(
			emp,
			get_first_day("2023-10-01"),
			get_last_day("2023-10-01"),
			"Monthly",
			payroll_period,
			depends_on_payment_days=0,
		)[1]

		prev_period = math.ceil(remaining_sub_periods)

		monthly_tax_amount = 7774.0
		monthly_earnings = 77800

		# Get Salary Structure Assignment
		ssa = frappe.get_value(
			"Salary Structure Assignment",
			{"employee": emp, "salary_structure": salary_structure_doc.name},
			"name",
		)
		ssa_doc = frappe.get_doc("Salary Structure Assignment", ssa)

		# Set opening balance for earning and tax deduction in Salary Structure Assignment
		ssa_doc.taxable_earnings_till_date = monthly_earnings * prev_period
		ssa_doc.tax_deducted_till_date = monthly_tax_amount * prev_period
		ssa_doc.save()

		# Create Salary Slip
		salary_slip = make_salary_slip(
			salary_structure_doc.name, employee=employee_doc.name, posting_date=getdate("2023-10-01")
		)
		for deduction in salary_slip.deductions:
			if deduction.salary_component == "TDS":
				self.assertEqual(deduction.amount, 7691.0)

		frappe.db.sql("DELETE FROM `tabPayroll Period` where company = '_Test Company'")
		frappe.db.sql("DELETE FROM `tabIncome Tax Slab` where currency = 'INR'")

	def test_income_tax_breakup_fields(self):
		from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure

		frappe.db.delete("Income Tax Slab", {"currency": "INR"})
		emp = make_employee(
			"test_employee_ss_income_tax_breakup@salary.com",
			company="_Test Company",
			date_of_joining="2021-01-01",
		)

		payroll_period = frappe.get_last_doc("Payroll Period", filters={"company": "_Test Company"})
		create_tax_slab(payroll_period, effective_date=payroll_period.start_date, allow_tax_exemption=True)

		salary_structure_name = "Test Salary Structure to test Income Tax Breakup"
		if not frappe.db.exists("Salary Structure", salary_structure_name):
			salary_structure_doc = make_salary_structure(
				salary_structure_name,
				"Monthly",
				company="_Test Company",
				employee=emp,
				from_date=payroll_period.start_date,
				payroll_period=payroll_period,
				test_tax=True,
				base=65000,
			)

		create_exemption_declaration(emp, payroll_period.name)

		create_additional_salary_for_non_taxable_component(emp, payroll_period, company="_Test Company")

		create_employee_other_income(emp, payroll_period.name, company="_Test Company")

		# Create Salary Slip
		salary_slip = make_salary_slip(
			salary_structure_doc.name, employee=emp, posting_date=payroll_period.start_date
		)

		monthly_tax_amount = 11403.6

		self.assertEqual(salary_slip.ctc, 1216000.0)
		self.assertEqual(salary_slip.income_from_other_sources, 10000.0)
		self.assertEqual(salary_slip.non_taxable_earnings, 10000.0)
		self.assertEqual(salary_slip.total_earnings, 1226000.0)
		self.assertEqual(salary_slip.standard_tax_exemption_amount, 50000.0)
		self.assertEqual(salary_slip.tax_exemption_declaration, 100000.0)
		self.assertEqual(salary_slip.deductions_before_tax_calculation, 2400.0)
		self.assertEqual(salary_slip.annual_taxable_amount, 1063600.0)
		self.assertEqual(flt(salary_slip.income_tax_deducted_till_date, 2), monthly_tax_amount)
		self.assertEqual(flt(salary_slip.current_month_income_tax, 2), monthly_tax_amount)
		self.assertEqual(flt(salary_slip.future_income_tax_deductions, 2), 125439.65)
		self.assertEqual(flt(salary_slip.total_income_tax, 2), 136843.25)

	def test_income_tax_breakup_when_tax_added_via_additional_salary(self):
		from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure

		frappe.db.delete("Income Tax Slab", {"currency": "INR"})
		emp = make_employee(
			"test_employee_ss_income_tax_breakup_added_via_addnl_salary@salary.com",
			company="_Test Company",
			date_of_joining="2021-01-01",
		)

		payroll_period = frappe.get_last_doc("Payroll Period", filters={"company": "_Test Company"})
		create_tax_slab(payroll_period, effective_date=payroll_period.start_date, allow_tax_exemption=True)

		salary_structure_name = "Test Salary Structure to test Income Tax Breakup added via addnl salary"
		if not frappe.db.exists("Salary Structure", salary_structure_name):
			salary_structure_doc = make_salary_structure(
				salary_structure_name,
				"Monthly",
				company="_Test Company",
				employee=emp,
				from_date=payroll_period.start_date,
				payroll_period=payroll_period,
				test_tax=True,
				base=65000,
			)

		create_exemption_declaration(emp, payroll_period.name)

		create_additional_salary_for_non_taxable_component(emp, payroll_period, company="_Test Company")

		# create TDS of 12000 via addnl salary doctype
		create_additional_salary_for_income_tax(emp, payroll_period, company="_Test Company")

		create_employee_other_income(emp, payroll_period.name, company="_Test Company")

		# Create Salary Slip
		salary_slip = make_salary_slip(
			salary_structure_doc.name, employee=emp, posting_date=payroll_period.start_date
		)

		monthly_tax_amount = 12000  # as 12000 is passed in addnl salary creation

		self.assertEqual(salary_slip.ctc, 1216000.0)
		self.assertEqual(salary_slip.income_from_other_sources, 10000.0)
		self.assertEqual(salary_slip.non_taxable_earnings, 10000.0)
		self.assertEqual(salary_slip.total_earnings, 1226000.0)
		self.assertEqual(salary_slip.standard_tax_exemption_amount, 50000.0)
		self.assertEqual(salary_slip.tax_exemption_declaration, 100000.0)
		self.assertEqual(salary_slip.deductions_before_tax_calculation, 2400.0)
		self.assertEqual(salary_slip.annual_taxable_amount, 1063600.0)
		self.assertEqual(flt(salary_slip.income_tax_deducted_till_date, 2), monthly_tax_amount)
		self.assertEqual(flt(salary_slip.current_month_income_tax, 2), monthly_tax_amount)
		self.assertEqual(flt(salary_slip.future_income_tax_deductions, 2), 124843.25)  # as 136843.25 - 12000
		self.assertEqual(flt(salary_slip.total_income_tax, 2), 136843.25)

	def test_consistent_future_earnings_irrespective_of_payment_days(self):
		"""
		For CTC calculation, verifies that future non taxable earnings remain
		consistent irrespective of the payment days of current month
		"""
		salary_slip = make_salary_slip_with_non_taxable_component()
		salary_slip.save()
		future_non_taxable_earnings_with_full_payment_days = (
			salary_slip.get_future_period_non_taxable_earnings()
		)

		salary_slip.payment_days = 20
		salary_slip.calculate_net_pay()
		future_non_taxable_earnings_with_reduced_payment_days = (
			salary_slip.get_future_period_non_taxable_earnings()
		)

		self.assertEqual(
			future_non_taxable_earnings_with_full_payment_days,
			future_non_taxable_earnings_with_reduced_payment_days,
		)

	def test_tax_period_for_mid_month_payroll_period(self):
		from hrms.payroll.doctype.payroll_period.payroll_period import get_period_factor

		frappe.db.delete("Payroll Period", {"company": "_Test Company"})
		payroll_period = create_payroll_period(
			name="Test Mid Month Payroll Period",
			company="_Test Company",
			start_date="2024-07-16",
			end_date="2025-07-15",
		)
		emp_id = make_employee("test_mid_month_payroll@salary.com")

		period_factor = get_period_factor(
			emp_id,
			"2024-07-16",
			"2024-08-15",
			"Monthly",
			payroll_period,
		)[1]

		# count the last month only if end date's day > start date's day
		# to handle cases like 16th Jul 2024 - 15th Jul 2025
		self.assertEqual(period_factor, 12)

	@change_settings("Payroll Settings", {"payroll_based_on": "Leave"})
	def test_lwp_calculation_based_on_relieving_date(self):
		emp_id = make_employee("test_lwp_based_on_relieving_date@salary.com")
		frappe.db.set_value("Employee", emp_id, {"relieving_date": None, "status": "Active"})
		frappe.db.set_value("Leave Type", "Leave Without Pay", "include_holiday", 0)

		month_start_date = get_first_day(nowdate())
		first_sunday = get_first_sunday(for_date=month_start_date)
		relieving_date = add_days(first_sunday, 10)
		leave_start_date = add_days(first_sunday, 16)
		leave_end_date = add_days(leave_start_date, 2)

		make_leave_application(emp_id, leave_start_date, leave_end_date, "Leave Without Pay")

		frappe.db.set_value("Employee", emp_id, {"relieving_date": relieving_date, "status": "Left"})

		ss = make_employee_salary_slip(
			emp_id,
			"Monthly",
			"Test Payment Based On Leave Application",
		)

		holidays = ss.get_holidays_for_employee(month_start_date, relieving_date)
		days_between_start_and_relieving = date_diff(relieving_date, month_start_date) + 1

		self.assertEqual(ss.leave_without_pay, 0)

		self.assertEqual(ss.payment_days, (days_between_start_and_relieving - len(holidays)))

	def test_zero_value_component(self):
		from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure

		emp = make_employee(
			"test_zero_value_component@salary.com",
			company="_Test Company",
			**{"date_of_joining": "2021-12-01"},
		)

		payroll_period = frappe.get_all("Payroll Period", filters={"company": "_Test Company"}, limit=1)
		payroll_period = frappe.get_cached_doc("Payroll Period", payroll_period[0].name)

		salary_structure_name = "Test zero value component"
		if not frappe.db.exists("Salary Structure", salary_structure_name):
			salary_structure_doc = make_salary_structure(
				salary_structure_name,
				"Monthly",
				company="_Test Company",
				employee=emp,
				from_date=payroll_period.start_date,
				payroll_period=payroll_period,
				base=65000,
			)

		# Create Salary Slip
		salary_slip = make_salary_slip(
			salary_structure_doc.name, employee=emp, posting_date=payroll_period.start_date
		)
		earnings = {d.salary_component: d.amount for d in salary_slip.earnings}

		# Check if zero value component is included in salary slip based on component settings
		self.assertIn("Arrear", earnings)
		self.assertEqual(earnings["Arrear"], 0.0)
		self.assertNotIn("Overtime", earnings)

	def test_component_default_amount_against_statistical_component(self):
		from hrms.payroll.doctype.salary_structure.test_salary_structure import (
			create_salary_structure_assignment,
		)

		emp = make_employee(
			"test_default_value_for_statistical_component@salary.com",
			company="_Test Company",
			**{"date_of_joining": "2021-12-01"},
		)

		salary_structure_doc = make_salary_structure_for_statistical_component("_Test Company")

		create_salary_structure_assignment(
			employee=emp,
			salary_structure=salary_structure_doc.name,
			company="_Test Company",
			currency="INR",
			base=40000,
		)

		# Create Salary Slip
		salary_slip = make_salary_slip(salary_structure_doc.name, employee=emp, posting_date=nowdate())

		for earning in salary_slip.earnings:
			if earning.salary_component == "Leave Travel Allowance":
				# formula for statistical component is, SC = base - BS - H
				# formula for Leave Travel Allowance is , LTA = base - SC
				# base = 40000
				# BS = base * 0.4 = 16000
				# H = 3000
				# SC = 40000 - 16000 - 3000 = 21000
				# LTA = 40000 - 21000 = 19000

				self.assertEqual(earning.default_amount, 19000)

	def test_variable_tax_component(self):
		from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure

		emp = make_employee(
			"testtaxcomponents@salary.com",
			company="_Test Company",
			**{"date_of_joining": "2021-12-01"},
		)

		salary_structure_name = "Test Tax Components"

		salary_structure_doc = make_salary_structure(
			salary_structure=salary_structure_name,
			payroll_frequency="Monthly",
			employee=emp,
			company="_Test Company",
			from_date=get_first_day(nowdate()),
			currency="INR",
			base=40000,
		)

		make_income_tax_components()

		salary_slip = make_salary_slip(salary_structure_doc.name, employee=emp, posting_date=nowdate())

		# check tax component not exist in salary slip
		self.assertNotIn("_Test TDS", [com.salary_component for com in salary_slip.deductions])

		# validate tax component is not configured as variable
		test_tds = frappe.get_doc("Salary Component", "_Test TDS")
		self.assertEqual(test_tds.variable_based_on_taxable_salary, 0)
		self.assertListEqual(test_tds.accounts, [])

		# configure company in tax component and set variable_based_on_taxable_salary as 1
		test_tds.append(
			"accounts",
			{
				"company": "_Test Company",
			},
		)
		test_tds.variable_based_on_taxable_salary = 1
		test_tds.save()

		# validate tax component is configurations
		self.assertEqual(test_tds.variable_based_on_taxable_salary, 1)
		self.assertIn("_Test Company", [com.company for com in test_tds.accounts])

		# define another tax component with variable_based_on_taxable_salary as 1 and company as empty
		income_tax = frappe.get_doc("Salary Component", "_Test Income Tax")
		income_tax.variable_based_on_taxable_salary = 1
		income_tax.save()

		self.assertEqual(income_tax.variable_based_on_taxable_salary, 1)

		# Validate tax component matching company criteria is added in salary slip
		tax_component = salary_slip.get_tax_components()
		self.assertEqual(test_tds.accounts[0].company, salary_slip.company)
		self.assertListEqual(tax_component, ["_Test TDS"])

	def test_opening_balances_excluded_from_tax_calculation(self):
		"""tests if opening balances in salary structure assignment are excluded from tax when assignment date is before payroll period"""
		from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure

		frappe.db.delete("Income Tax Slab", {"currency": "INR"})
		emp = make_employee(
			"test_opening_balances@salary.com",
			company="_Test Company",
			date_of_joining="2022-04-01",
		)

		payroll_period = create_payroll_period(
			name="_Test Opening Balance Payroll Period",
			company="_Test Company",
			start_date="2023-04-01",
			end_date="2024-03-31",
		)

		# create salary structure and assignment with from_date before payroll period
		salary_structure = make_salary_structure(
			"Test Opening Balance Structure",
			"Monthly",
			company="_Test Company",
			employee=emp,
			from_date="2022-04-01",
			payroll_period=payroll_period,
			test_tax=True,
			base=50000,
		)

		ssa = frappe.get_value(
			"Salary Structure Assignment",
			{"employee": emp, "salary_structure": salary_structure.name},
			"name",
		)
		ssa_doc = frappe.get_doc("Salary Structure Assignment", ssa)
		# Set opening tax balances in assignment
		ssa_doc.db_set("taxable_earnings_till_date", 600000)
		ssa_doc.db_set("tax_deducted_till_date", 45500)

		# Create salary slip
		salary_slip = make_salary_slip(salary_structure.name, employee=emp, posting_date="2023-04-01")

		# calculate expected taxable amount without opening balance
		# 50000 (base) + 28000 (other earnings from structure)
		monthly_taxable_earnings = 78000
		expected_annual_taxable_amount = monthly_taxable_earnings * 12

		# Verify that opening balance is not included in tax calculation
		self.assertNotEqual(
			salary_slip.annual_taxable_amount,
			expected_annual_taxable_amount + ssa_doc.taxable_earnings_till_date,
		)
		self.assertEqual(salary_slip.income_tax_deducted_till_date, salary_slip.current_month_income_tax)

	def test_tax_payable_with_tax_relief_and_marginal_relief_limits(self):
		from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure
		from hrms.regional.india.setup import setup

		setup()

		frappe.db.delete("Income Tax Slab", {"currency": "INR"})
		emp = make_employee(
			"test_employee_tax_relief@salary.com",
			company="_Test Company",
			date_of_joining="2021-01-01",
		)

		payroll_period = frappe.get_last_doc("Payroll Period", filters={"company": "_Test Company"})

		create_tax_slab(payroll_period, effective_date=payroll_period.start_date, apply_tax_relief=True)

		salary_structure_doc = make_salary_structure(
			"Test Tax Relief",
			"Monthly",
			company="_Test Company",
			employee=emp,
			payroll_period=payroll_period,
			test_tax=True,
			base=65000,
		)

		salary_slip = make_salary_slip(
			salary_structure_doc.name, employee=emp, posting_date=payroll_period.start_date
		)

		tax_relief_limit, marginal_relief_limit = frappe.db.get_value(
			"Income Tax Slab", {"currency": "INR"}, ["tax_relief_limit", "marginal_relief_limit"]
		)

		# taxable income within marginal relief limit
		self.assertGreater(marginal_relief_limit, salary_slip.annual_taxable_amount)

		# tax payable is reduced to income excess over tax relief limit
		total_income_tax = salary_slip.annual_taxable_amount - tax_relief_limit
		total_income_tax += total_income_tax * 0.04  # add cess

		self.assertEqual(salary_slip.total_income_tax, total_income_tax)

	def test_status_on_discard(self):
		salary_slip = make_salary_slip_with_non_taxable_component()
		salary_slip.save()
		salary_slip.discard()
		salary_slip.reload()
		self.assertEqual(salary_slip.status, "Cancelled")

	def test_salary_component_for_payment_days_zero(self):
		from hrms.payroll.doctype.salary_structure.test_salary_structure import (
			create_salary_structure_assignment,
			make_salary_structure,
		)

		emp = make_employee(
			"test_payment_days_zero_component@salary.com",
			company="_Test Company",
			**{"date_of_joining": "2021-12-01"},
		)

		payroll_period = frappe.get_all("Payroll Period", filters={"company": "_Test Company"}, limit=1)
		payroll_period = frappe.get_cached_doc("Payroll Period", payroll_period[0].name)

		data = [
			{
				"salary_component": "Basic",
				"abbr": "BS",
				"type": "Earning",
				"formula": "base",
				"amount_based_on_formula": 1,
				"depends_on_payment_days": 1,
			},
			{
				"salary_component": "House Rent Allowance",
				"abbr": "HRA",
				"type": "Earning",
				"formula": "BS * 0.5",
				"amount_based_on_formula": 1,
				"depends_on_payment_days": 0,
			},
		]
		make_salary_component(data, False, company_list=["_Test Company"])

		salary_structure_name = "Test Payment Days Zero Component"
		salary_structure_doc = make_salary_structure(
			salary_structure_name,
			"Monthly",
			company="_Test Company",
			employee=emp,
			from_date=payroll_period.start_date,
			payroll_period=payroll_period,
			base=65000,
		)

		create_salary_structure_assignment(
			emp,
			salary_structure_doc.name,
			from_date=payroll_period.start_date,
			company="_Test Company",
			currency="INR",
			payroll_period=payroll_period,
			base=65000,
		)

		salary_slip = make_salary_slip(
			salary_structure_doc.name, employee=emp, posting_date=payroll_period.start_date
		)
		salary_slip.payment_days = 0

		earnings = {d.salary_component: d for d in salary_slip.earnings}

		self.assertNotIn("Basic", earnings)

		self.assertNotIn("House Rent Allowance", earnings)

	def test_salary_component_for_additional_salary_zero(self):
		from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure

		emp = make_employee(
			"test_zero_value_component@salary.com",
			company="_Test Company",
			**{"date_of_joining": "2021-12-01"},
		)

		payroll_period = frappe.get_all("Payroll Period", filters={"company": "_Test Company"}, limit=1)
		payroll_period = frappe.get_cached_doc("Payroll Period", payroll_period[0].name)

		data = [
			{
				"salary_component": "Allowance",
				"abbr": "ALL",
				"type": "Earning",
				"is_income_tax_component": 0,
				"amount": 350,
			},
		]
		make_salary_component(data, False, company_list=["_Test Company"])

		salary_structure_name = "Test Additional Salary component"
		salary_structure_doc = make_salary_structure(
			salary_structure_name,
			"Monthly",
			company="_Test Company",
			employee=emp,
			from_date=payroll_period.start_date,
			payroll_period=payroll_period,
			base=65000,
		)

		frappe.get_doc(
			{
				"doctype": "Additional Salary",
				"employee": emp,
				"company": "_Test Company",
				"salary_component": "Allowance",
				"overwrite_salary_structure_amount": 1,
				"amount": 0,
				"payroll_date": payroll_period.start_date,
				"currency": erpnext.get_default_currency(),
			}
		).submit()

		salary_slip = make_salary_slip(
			salary_structure_doc.name, employee=emp, posting_date=payroll_period.start_date
		)
		earnings = {d.salary_component: d.amount for d in salary_slip.earnings}

		self.assertIn("Allowance", earnings)
		self.assertEqual(earnings["Allowance"], 0.0)


class TestSalarySlipSafeEval(IntegrationTestCase):
	def test_safe_eval_for_salary_slip(self):
		TEST_CASES = {
			"1+1": 2,
			'"abc" in "abl"': False,
			'"a" in "abl"': True,
			'"a" in ("a", "b")': True,
			'"a" in {"a", "b"}': True,
			'"a" in {"a": 1, "b": 2}': True,
			'"a" in ["a" ,"b"]': True,
		}

		for code, result in TEST_CASES.items():
			self.assertEqual(_safe_eval(code), result)

		self.assertRaises(NameError, _safe_eval, "frappe.utils.os.path", {})

		# Doc/dict objects
		user = frappe.new_doc("User")
		user.user_type = "System User"
		user.enabled = 1
		self.assertTrue(_safe_eval("user_type == 'System User'", eval_locals=user.as_dict()))
		self.assertEqual("System User Test", _safe_eval("user_type + ' Test'", eval_locals=user.as_dict()))
		self.assertEqual(1, _safe_eval("int(enabled)", eval_locals=user.as_dict()))

		# Walrus not allowed
		self.assertRaises(SyntaxError, _safe_eval, "(x := (40+2))")

		# Format check but saner
		self.assertTrue(_safe_eval("'x' != 'Information Techonology'"))
		self.assertRaises(SyntaxError, _safe_eval, "'blah'.format(1)")


def make_income_tax_components():
	tax_components = [
		{
			"salary_component": "_Test TDS",
			"abbr": "T_TDS",
			"type": "Deduction",
			"depends_on_payment_days": 0,
			"variable_based_on_taxable_salary": 0,
			"round_to_the_nearest_integer": 1,
		},
		{
			"salary_component": "_Test Income Tax",
			"abbr": "T_IT",
			"type": "Deduction",
			"depends_on_payment_days": 0,
			"variable_based_on_taxable_salary": 0,
			"round_to_the_nearest_integer": 1,
		},
	]
	make_salary_component(tax_components, False, company_list=[])


def get_no_of_days():
	no_of_days_in_month = calendar.monthrange(getdate(nowdate()).year, getdate(nowdate()).month)
	no_of_holidays_in_month = len(
		[1 for i in calendar.monthcalendar(getdate(nowdate()).year, getdate(nowdate()).month) if i[6] != 0]
	)

	return [no_of_days_in_month[1], no_of_holidays_in_month]


def make_employee_salary_slip(
	emp_id: str,
	payroll_frequency: str,
	salary_structure: str | None = None,
	posting_date: str | None = None,
	payroll_period: dict | None = None,
) -> dict:
	from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure

	if not salary_structure:
		salary_structure = payroll_frequency + " Salary Structure Test for Salary Slip"

	employee = frappe.db.get_value("Employee", emp_id, ["name", "company", "employee_name"], as_dict=True)

	salary_structure_doc = make_salary_structure(
		salary_structure,
		payroll_frequency,
		employee=employee.name,
		company=employee.company,
		from_date=posting_date,
		payroll_period=payroll_period,
	)
	salary_slip_name = frappe.db.get_value("Salary Slip", {"employee": emp_id})

	if not salary_slip_name:
		date = posting_date or nowdate()
		salary_slip = make_salary_slip(salary_structure_doc.name, employee=employee.name, posting_date=date)
		salary_slip.employee_name = employee.employee_name
		salary_slip.payroll_frequency = payroll_frequency
		salary_slip.posting_date = date
		salary_slip.insert()
	else:
		salary_slip = frappe.get_doc("Salary Slip", salary_slip_name)

	return salary_slip


def make_salary_component(salary_components, test_tax, company_list=None):
	for salary_component in salary_components:
		if frappe.db.exists("Salary Component", salary_component["salary_component"]):
			frappe.delete_doc("Salary Component", salary_component["salary_component"], force=True)

		if test_tax:
			if salary_component["type"] == "Earning":
				salary_component["is_tax_applicable"] = 1
			elif salary_component["salary_component"] == "TDS":
				salary_component["variable_based_on_taxable_salary"] = 1
				salary_component["amount_based_on_formula"] = 0
				salary_component["amount"] = 0
				salary_component["formula"] = ""
				salary_component["condition"] = ""

		salary_component["salary_component_abbr"] = salary_component["abbr"]
		if salary_component.get("arrear_component"):
			salary_component["arrear_component"] = 1
		doc = frappe.new_doc("Salary Component")
		doc.update(salary_component)
		doc.insert()

		set_salary_component_account(doc, company_list)


def set_salary_component_account(sal_comp, company_list=None):
	company = erpnext.get_default_company()

	if company_list and company and company not in company_list:
		company_list.append(company)

	if not isinstance(sal_comp, Document):
		sal_comp = frappe.get_doc("Salary Component", sal_comp)

	if not sal_comp.get("accounts"):
		for d in company_list:
			company_abbr = frappe.get_cached_value("Company", d, "abbr")

			if sal_comp.type == "Earning":
				account_name = "Salary"
				parent_account = "Indirect Expenses - " + company_abbr
			else:
				account_name = "Salary Deductions"
				parent_account = "Current Liabilities - " + company_abbr

			sal_comp.append(
				"accounts", {"company": d, "account": create_account(account_name, d, parent_account)}
			)
			sal_comp.save()


def create_account(account_name, company, parent_account, account_type=None):
	company_abbr = frappe.get_cached_value("Company", company, "abbr")
	account = frappe.db.get_value("Account", account_name + " - " + company_abbr)
	if not account:
		frappe.get_doc(
			{
				"doctype": "Account",
				"account_name": account_name,
				"parent_account": parent_account,
				"company": company,
			}
		).insert()
	return account


def make_earning_salary_component(
	setup=False,
	test_tax=False,
	company_list=None,
	test_accrual_component=False,
	test_arrear=False,
	test_statistical_comp=False,
):
	data = [
		{
			"salary_component": "Basic Salary",
			"abbr": "BS",
			"condition": "base > 10000",
			"formula": "base",
			"type": "Earning",
			"amount_based_on_formula": 1,
			"arrear_component": 1 if test_arrear else 0,
			"depends_on_payment_days": 1,
		},
		{"salary_component": "HRA", "abbr": "H", "amount": 3000, "type": "Earning"},
		{
			"salary_component": "Special Allowance",
			"abbr": "SA",
			"condition": "H < 10000",
			# intentional to test multiline formula
			"formula": "BS\n*.5",
			"type": "Earning",
			"amount_based_on_formula": 1,
			"depends_on_payment_days": 0,
			"arrear_component": 1 if test_arrear else 0,
		},
		{"salary_component": "Leave Encashment", "abbr": "LE", "type": "Earning"},
		{
			"salary_component": "Statistical Component",
			"abbr": "SC",
			"type": "Earning",
			"statistical_component": 1,
			"amount": 500,
		},
		{
			"salary_component": "Arrear",
			"abbr": "A",
			"type": "Earning",
			"depends_on_payment_days": 0,
			"amount": 0,
			"remove_if_zero_valued": 0,
		},
		{
			"salary_component": "Overtime",
			"abbr": "OT",
			"type": "Earning",
			"depends_on_payment_days": 0,
			"amount": 0,
			"remove_if_zero_valued": 1,
		},
		{
			"salary_component": "Recurring Salary Component",
			"abbr": "RSC",
			"type": "Earning",
			"depends_on_payment_days": 0,
			"amount": 0,
			"remove_if_zero_valued": 1,
		},
	]

	if test_accrual_component:
		data.extend(
			[
				{
					"salary_component": "Accrued Earnings",
					"abbr": "AC",
					"type": "Earning",
					"accrual_component": 1,
					"amount": 1000,
					"arrear_component": 1,
				}
			]
		)

	if test_tax:
		data.extend(
			[
				{"salary_component": "Performance Bonus", "abbr": "B", "type": "Earning"},
			]
		)

	if setup or test_tax:
		make_salary_component(data, test_tax, company_list)

	data.append(
		{
			"salary_component": "Basic Salary",
			"abbr": "BS",
			"condition": "base < 10000",
			"formula": "base*.2",
			"type": "Earning",
			"amount_based_on_formula": 1,
		}
	)
	return data


def make_deduction_salary_component(
	setup=False, test_tax=False, company_list=None, test_salary_structure_arrear=False
):
	data = [
		{
			"salary_component": "Professional Tax",
			"abbr": "PT",
			"type": "Deduction",
			"amount": 300
			if test_salary_structure_arrear
			else 200,  # setting a different amount to test salary structure arrear calculation
			"exempted_from_income_tax": 1,
			"arrear_component": 1,
		}
	]
	if not test_tax:
		data.append(
			{
				"salary_component": "TDS",
				"abbr": "T",
				"condition": 'employment_type=="Intern"',
				"type": "Deduction",
				"round_to_the_nearest_integer": 1,
			}
		)
	else:
		data.append(
			{
				"salary_component": "TDS",
				"abbr": "T",
				"type": "Deduction",
				"depends_on_payment_days": 0,
				"variable_based_on_taxable_salary": 1,
				"is_income_tax_component": 1,
				"round_to_the_nearest_integer": 1,
			}
		)
	if setup or test_tax:
		make_salary_component(data, test_tax, company_list)

	return data


def make_employee_benefit_earning_components(
	setup=False, test_tax=False, company_list=None, test_arrear=False
):
	if setup:
		data = [
			{
				"salary_component": "Leave Travel Allowance",
				"abbr": "LTA",
				"is_flexible_benefit": 1,
				"type": "Earning",
				"payout_method": "Allow claim for full benefit amount",
				"max_benefit_amount": 50000,
				"accrual_component": 0,
			},
			{
				"salary_component": "Mediclaim Allowance",
				"abbr": "MA",
				"is_flexible_benefit": 1,
				"type": "Earning",
				"payout_method": "Accrue per cycle, pay only on claim",
				"final_cycle_accrual_payout": 1,
				"accrual_component": 1,
			},
			{
				"salary_component": "Internet Reimbursement",
				"abbr": "IR",
				"is_flexible_benefit": 1,
				"type": "Earning",
				"payout_method": "Accrue and payout at end of payroll period",
				"accrual_component": 1,
			},
		]

		if test_arrear:
			data[1].update(
				{
					"arrear_component": 1,
					"depends_on_payment_days": 1,
				}
			)

		make_salary_component(data, test_tax, company_list)

	data = [
		{
			"salary_component": "Leave Travel Allowance",
			"amount": 50000,
		},
		{
			"salary_component": "Mediclaim Allowance",
			"amount": 24000,
		},
		{
			"salary_component": "Internet Reimbursement",
			"amount": 12000,
		},
	]

	return data


def get_tax_paid_in_period(employee):
	tax_paid_amount = frappe.db.sql(
		"""select sum(sd.amount) from `tabSalary Detail`
		sd join `tabSalary Slip` ss where ss.name=sd.parent and ss.employee=%s
		and ss.docstatus=1 and sd.salary_component='TDS'""",
		(employee),
	)
	return tax_paid_amount[0][0]


def create_exemption_declaration(employee, payroll_period):
	create_exemption_category()
	declaration = frappe.get_doc(
		{
			"doctype": "Employee Tax Exemption Declaration",
			"employee": employee,
			"payroll_period": payroll_period,
			"company": erpnext.get_default_company(),
			"currency": erpnext.get_default_currency(),
		}
	)
	declaration.append(
		"declarations",
		{
			"exemption_sub_category": "_Test Sub Category",
			"exemption_category": "_Test Category",
			"amount": 100000,
		},
	)
	declaration.submit()


def create_proof_submission(employee, payroll_period, amount):
	submission_date = add_months(payroll_period.start_date, random.randint(0, 11))
	proof_submission = frappe.get_doc(
		{
			"doctype": "Employee Tax Exemption Proof Submission",
			"employee": employee,
			"payroll_period": payroll_period.name,
			"submission_date": submission_date,
			"currency": erpnext.get_default_currency(),
		}
	)
	proof_submission.append(
		"tax_exemption_proofs",
		{
			"exemption_sub_category": "_Test Sub Category",
			"exemption_category": "_Test Category",
			"type_of_proof": "Test",
			"amount": amount,
		},
	)
	proof_submission.submit()
	return submission_date


def create_tax_slab(
	payroll_period,
	effective_date=None,
	allow_tax_exemption=False,
	dont_submit=False,
	currency=None,
	company=None,
	apply_tax_relief=False,
):
	if not currency:
		currency = erpnext.get_default_currency()

	if company:
		currency = erpnext.get_company_currency(company)

	slabs = [
		{
			"from_amount": 250000,
			"to_amount": 500000,
			"percent_deduction": 5,
			"condition": "annual_taxable_earning > 500000",
		},
		{"from_amount": 500001, "to_amount": 1000000, "percent_deduction": 20},
		{"from_amount": 1000001, "percent_deduction": 30},
	]

	income_tax_slab_name = frappe.db.get_value("Income Tax Slab", {"currency": currency, "docstatus": 1})

	if not income_tax_slab_name:
		income_tax_slab = frappe.new_doc("Income Tax Slab")
		income_tax_slab.name = "Tax Slab: " + payroll_period.name + " " + cstr(currency)
		income_tax_slab.effective_from = effective_date or add_days(payroll_period.start_date, -2)
		income_tax_slab.company = company or ""
		income_tax_slab.currency = currency

		if allow_tax_exemption:
			income_tax_slab.allow_tax_exemption = 1
			income_tax_slab.standard_tax_exemption_amount = 50000

		for item in slabs:
			income_tax_slab.append("slabs", item)

		income_tax_slab.append("other_taxes_and_charges", {"description": "cess", "percent": 4})

		if apply_tax_relief:
			income_tax_slab.tax_relief_limit = 1200000
			income_tax_slab.marginal_relief_limit = 1275000

		income_tax_slab.save()
		if not dont_submit:
			income_tax_slab.submit()

		return income_tax_slab.name
	else:
		return income_tax_slab_name


def create_salary_slips_for_payroll_period(
	employee, salary_structure, payroll_period, deduct_random=True, num=12
):
	deducted_dates = []
	i = 0
	while i < num:
		slip = frappe.get_doc(
			{
				"doctype": "Salary Slip",
				"employee": employee,
				"salary_structure": salary_structure,
				"frequency": "Monthly",
			}
		)
		if i == 0:
			posting_date = add_days(payroll_period.start_date, 25)
		else:
			posting_date = add_months(posting_date, 1)
		if i == 11:
			slip.deduct_tax_for_unsubmitted_tax_exemption_proof = 1
		if deduct_random and not random.randint(0, 2):
			slip.deduct_tax_for_unsubmitted_tax_exemption_proof = 1
			deducted_dates.append(posting_date)
		slip.posting_date = posting_date
		slip.start_date = get_first_day(posting_date)
		slip.end_date = get_last_day(posting_date)
		doc = make_salary_slip(salary_structure, slip, employee)
		doc.submit()
		i += 1
	return deducted_dates


def create_additional_salary(employee, payroll_period, amount):
	salary_date = add_months(payroll_period.start_date, random.randint(0, 11))
	frappe.get_doc(
		{
			"doctype": "Additional Salary",
			"employee": employee,
			"company": erpnext.get_default_company(),
			"salary_component": "Performance Bonus",
			"payroll_date": salary_date,
			"amount": amount,
			"type": "Earning",
			"currency": erpnext.get_default_currency(),
		}
	).submit()
	return salary_date


def make_leave_application(
	employee,
	from_date,
	to_date,
	leave_type,
	company=None,
	half_day=False,
	half_day_date=None,
	submit=True,
):
	create_user("test@example.com")

	leave_application = frappe.get_doc(
		dict(
			doctype="Leave Application",
			employee=employee,
			leave_type=leave_type,
			from_date=from_date,
			to_date=to_date,
			half_day=half_day,
			half_day_date=half_day_date,
			company=company or erpnext.get_default_company() or "_Test Company",
			status="Approved",
			leave_approver="test@example.com",
		)
	).insert()

	if submit:
		leave_application.submit()

	return leave_application


def setup_test():
	make_earning_salary_component(setup=True, company_list=["_Test Company"])
	make_deduction_salary_component(setup=True, company_list=["_Test Company"])

	for dt in [
		"Leave Application",
		"Leave Allocation",
		"Salary Slip",
		"Attendance",
		"Additional Salary",
		"Employee Tax Exemption Declaration",
		"Employee Tax Exemption Proof Submission",
		"Employee Benefit Claim",
		"Salary Structure Assignment",
		"Payroll Period",
	]:
		frappe.db.sql("delete from `tab%s`" % dt)

	make_holiday_list()
	make_payroll_period()

	frappe.db.set_value(
		"Company", erpnext.get_default_company(), "default_holiday_list", "Salary Slip Test Holiday List"
	)

	frappe.db.set_single_value("Payroll Settings", "email_salary_slip_to_employee", 0)
	frappe.db.set_single_value("HR Settings", "leave_status_notification_template", None)
	frappe.db.set_single_value("HR Settings", "leave_approval_notification_template", None)


def make_payroll_period():
	default_company = erpnext.get_default_company()
	company_based_payroll_period = {
		default_company: f"_Test Payroll Period {default_company}",
		"_Test Company": "_Test Payroll Period",
	}
	for company in company_based_payroll_period:
		payroll_period = frappe.db.get_value(
			"Payroll Period",
			{
				"company": company,
				"start_date": get_year_start(nowdate()),
				"end_date": get_year_ending(nowdate()),
			},
		)

		if not payroll_period:
			create_payroll_period(company=company, name=company_based_payroll_period[company])


def make_holiday_list(
	list_name=None, from_date=None, to_date=None, add_weekly_offs=True, weekly_off_days=None
):
	fiscal_year = get_fiscal_year(nowdate(), company=erpnext.get_default_company())
	name = list_name or "Salary Slip Test Holiday List"

	frappe.delete_doc_if_exists("Holiday List", name, force=True)

	holiday_list = frappe.get_doc(
		{
			"doctype": "Holiday List",
			"holiday_list_name": name,
			"from_date": from_date or fiscal_year[1],
			"to_date": to_date or fiscal_year[2],
		}
	).insert()

	if add_weekly_offs:
		if not weekly_off_days:
			weekly_off_days = ["Sunday"]
		for d in weekly_off_days:
			holiday_list.weekly_off = d
			holiday_list.get_weekly_off_dates()

	holiday_list.save()
	holiday_list = holiday_list.name

	return holiday_list


def make_salary_structure_for_payment_days_based_component_dependency(test_statistical_comp=False):
	earnings = [
		{
			"salary_component": "Basic Salary - Payment Days",
			"abbr": "P_BS",
			"type": "Earning",
			"formula": "base",
			"amount_based_on_formula": 1,
		},
		{
			"salary_component": "HRA - Payment Days",
			"abbr": "P_HRA",
			"type": "Earning",
			"depends_on_payment_days": 1,
			"amount_based_on_formula": 1,
			"formula": "base * 0.20",
		},
	]
	if test_statistical_comp:
		earnings.extend(
			[
				{
					"salary_component": "Statistical Component",
					"abbr": "SC",
					"type": "Earning",
					"statistical_component": 1,
					"amount": 1000,
					"depends_on_payment_days": 1,
				},
				{
					"salary_component": "Dependency Component",
					"abbr": "DC",
					"type": "Earning",
					"amount_based_on_formula": 1,
					"formula": "SC * 0.5",
					"depends_on_payment_days": 0,
				},
			]
		)

	make_salary_component(earnings, False, company_list=["_Test Company"])

	deductions = [
		{
			"salary_component": "P - Professional Tax",
			"abbr": "P_PT",
			"type": "Deduction",
			"depends_on_payment_days": 1,
			"amount": 200.00,
		},
		{
			"salary_component": "P - Employee Provident Fund",
			"abbr": "P_EPF",
			"type": "Deduction",
			"exempted_from_income_tax": 1,
			"amount_based_on_formula": 1,
			"depends_on_payment_days": 0,
			"formula": "(gross_pay - P_HRA) * 0.12",
		},
	]

	make_salary_component(deductions, False, company_list=["_Test Company"])

	salary_structure = "Salary Structure with PF"
	if frappe.db.exists("Salary Structure", salary_structure):
		frappe.db.delete("Salary Structure", salary_structure)

	details = {
		"doctype": "Salary Structure",
		"name": salary_structure,
		"company": "_Test Company",
		"payroll_frequency": "Monthly",
		"payment_account": get_random("Account", filters={"account_currency": "INR"}),
		"currency": "INR",
	}

	salary_structure_doc = frappe.get_doc(details)

	for entry in earnings:
		salary_structure_doc.append("earnings", entry)

	for entry in deductions:
		salary_structure_doc.append("deductions", entry)

	salary_structure_doc.insert()
	salary_structure_doc.submit()

	return salary_structure_doc


def make_salary_slip_for_payment_days_dependency_test(employee, salary_structure):
	employee = frappe.db.get_value(
		"Employee", {"user_id": employee}, ["name", "company", "employee_name"], as_dict=True
	)

	salary_slip_name = frappe.db.get_value("Salary Slip", {"employee": employee.name})

	if not salary_slip_name:
		salary_slip = make_salary_slip(salary_structure, employee=employee.name)
		salary_slip.employee_name = employee.employee_name
		salary_slip.payroll_frequency = "Monthly"
		salary_slip.posting_date = nowdate()
		salary_slip.insert()
	else:
		salary_slip = frappe.get_doc("Salary Slip", salary_slip_name)

	return salary_slip


def create_recurring_additional_salary(employee, salary_component, amount, from_date, to_date, company=None):
	frappe.get_doc(
		{
			"doctype": "Additional Salary",
			"employee": employee,
			"company": company or erpnext.get_default_company(),
			"salary_component": salary_component,
			"is_recurring": 1,
			"from_date": from_date,
			"to_date": to_date,
			"amount": amount,
			"type": "Earning",
			"currency": erpnext.get_default_currency(),
		}
	).submit()


def make_salary_structure_for_timesheet(employee, company=None):
	from hrms.payroll.doctype.salary_structure.test_salary_structure import (
		create_salary_structure_assignment,
		make_salary_structure,
	)

	salary_structure_name = "Timesheet Salary Structure Test"
	frequency = "Monthly"

	if not frappe.db.exists("Salary Component", "Timesheet Component"):
		frappe.get_doc({"doctype": "Salary Component", "salary_component": "Timesheet Component"}).insert()

	salary_structure = make_salary_structure(
		salary_structure_name, frequency, company=company, dont_submit=True
	)
	salary_structure.salary_component = "Timesheet Component"
	salary_structure.salary_slip_based_on_timesheet = 1
	salary_structure.hour_rate = 50.0
	salary_structure.save()
	salary_structure.submit()

	if not frappe.db.get_value("Salary Structure Assignment", {"employee": employee, "docstatus": 1}):
		frappe.db.set_value("Employee", employee, "date_of_joining", add_months(nowdate(), -5))
		create_salary_structure_assignment(employee, salary_structure.name)

	return salary_structure


def create_employee_other_income(employee, payroll_period, company):
	other_income = frappe.db.get_value(
		"Employee Other Income",
		{
			"employee": employee,
			"payroll_period": payroll_period,
			"company": company,
			"docstatus": 1,
		},
		"name",
	)

	if not other_income:
		other_income = frappe.get_doc(
			{
				"doctype": "Employee Other Income",
				"employee": employee,
				"payroll_period": payroll_period,
				"company": company,
				"source": "Other Income",
				"amount": 10000,
			}
		).insert()

		other_income.submit()

	return other_income


def create_additional_salary_for_non_taxable_component(employee, payroll_period, company):
	data = [
		{
			"salary_component": "Non Taxable Additional Salary",
			"abbr": "AS",
			"type": "Earning",
			"is_tax_applicable": 0,
		},
	]
	make_salary_component(data, False, company_list=[company])

	add_sal = frappe.get_doc(
		{
			"doctype": "Additional Salary",
			"employee": employee,
			"company": company,
			"salary_component": "Non Taxable Additional Salary",
			"overwrite_salary_structure_amount": 0,
			"amount": 10000,
			"currency": "INR",
			"payroll_date": payroll_period.start_date,
		}
	).insert()

	add_sal.submit()


def create_additional_salary_for_income_tax(employee, payroll_period, company):
	data = [
		{
			"salary_component": "TDS",
			"abbr": "T",
			"type": "Deduction",
			"is_income_tax_component": 1,
		},
	]
	make_salary_component(data, True, company_list=[company])

	add_sal = frappe.get_doc(
		{
			"doctype": "Additional Salary",
			"employee": employee,
			"company": company,
			"salary_component": "TDS",
			"overwrite_salary_structure_amount": 1,
			"amount": 12000,
			"currency": "INR",
			"payroll_date": payroll_period.start_date,
		}
	).insert()
	add_sal.submit()


def make_salary_structure_for_statistical_component(company):
	earnings = [
		{
			"salary_component": "Basic Component",
			"abbr": "BSC",
			"formula": "base * 0.4",
			"type": "Earning",
			"amount_based_on_formula": 1,
		},
		{"salary_component": "HRA Component", "abbr": "HRAC", "amount": 3000, "type": "Earning"},
		{
			"salary_component": "Statistical Component",
			"abbr": "SC",
			"type": "Earning",
			"formula": "base - BSC - HRAC",
			"statistical_component": 1,
			"amount_based_on_formula": 1,
			"depends_on_payment_days": 0,
		},
		{
			"salary_component": "Leave Travel Allowance",
			"abbr": "LTA",
			"formula": "base - SC",
			"type": "Earning",
			"amount_based_on_formula": 1,
			"depends_on_payment_days": 0,
		},
	]

	make_salary_component(earnings, False, company_list=[company])

	deductions = [
		{
			"salary_component": "P - Professional Tax",
			"abbr": "P_PT",
			"type": "Deduction",
			"depends_on_payment_days": 1,
			"amount": 200.00,
		},
	]

	make_salary_component(deductions, False, company_list=["_Test Company"])

	salary_structure = "Salary Structure with Statistical Component"
	if frappe.db.exists("Salary Structure", salary_structure):
		frappe.db.delete("Salary Structure", salary_structure)

	details = {
		"doctype": "Salary Structure",
		"name": salary_structure,
		"company": "_Test Company",
		"payroll_frequency": "Monthly",
		"payment_account": get_random("Account", filters={"account_currency": "INR"}),
		"currency": "INR",
	}

	salary_structure_doc = frappe.get_doc(details)

	for entry in earnings:
		salary_structure_doc.append("earnings", entry)

	for entry in deductions:
		salary_structure_doc.append("deductions", entry)

	salary_structure_doc.insert()
	salary_structure_doc.submit()

	return salary_structure_doc


def make_salary_slip_with_non_taxable_component() -> SalarySlip:
	from hrms.payroll.doctype.salary_structure.test_salary_structure import (
		create_salary_structure_assignment,
		make_salary_structure,
	)

	frappe.db.delete("Income Tax Slab", {"currency": "INR"})
	emp = make_employee(
		"test_employee_ss_income_tax_breakup@salary.com",
		company="_Test Company",
		date_of_joining="2021-01-01",
	)

	payroll_period = frappe.get_last_doc("Payroll Period", filters={"company": "_Test Company"})
	create_tax_slab(payroll_period, effective_date=payroll_period.start_date, allow_tax_exemption=True)

	earnings = [
		{
			"salary_component": "Basic Salary",
			"abbr": "P_BS",
			"type": "Earning",
			"formula": "base",
			"amount_based_on_formula": 1,
		},
		# non taxable component
		{
			"salary_component": "Children Education Allowance",
			"abbr": "CH_EDU",
			"type": "Earning",
			"depends_on_payment_days": 1,
			"amount_based_on_formula": 1,
			"formula": "base * 0.20",
			"is_tax_applicable": 0,
		},
	]
	make_salary_component(earnings, False, company_list=["_Test Company"])

	deductions = [
		{
			"salary_component": "P - Professional Tax",
			"abbr": "P_PT",
			"type": "Deduction",
			"depends_on_payment_days": 1,
			"amount": 200.00,
		},
	]
	make_salary_component(deductions, False, company_list=["_Test Company"])

	salary_structure = "Salary Structure with Non Taxable Component"
	if frappe.db.exists("Salary Structure", salary_structure):
		frappe.db.delete("Salary Structure", salary_structure)

	details = {
		"doctype": "Salary Structure",
		"name": salary_structure,
		"company": "_Test Company",
		"payroll_frequency": "Monthly",
		"payment_account": get_random("Account", filters={"account_currency": "INR"}),
		"currency": "INR",
	}

	salary_structure_doc = frappe.get_doc(details)

	for entry in earnings:
		salary_structure_doc.append("earnings", entry)

	for entry in deductions:
		salary_structure_doc.append("deductions", entry)

	salary_structure_doc.insert().submit()
	create_salary_structure_assignment(
		emp,
		salary_structure_doc.name,
		from_date=payroll_period.start_date,
		company="_Test Company",
		currency="INR",
		payroll_period=payroll_period,
		base=65000,
	)

	# Create Salary Slip
	salary_slip = make_salary_slip(
		salary_structure_doc.name, employee=emp, posting_date=payroll_period.start_date
	)
	return salary_slip


def mark_attendance(
	employee,
	attendance_date,
	status,
	shift=None,
	ignore_validate=False,
	leave_type=None,
	late_entry=False,
	early_exit=False,
	half_day_status=None,
):
	attendance = frappe.new_doc("Attendance")
	attendance.update(
		{
			"doctype": "Attendance",
			"employee": employee,
			"attendance_date": attendance_date,
			"status": status,
			"shift": shift,
			"leave_type": leave_type,
			"late_entry": late_entry,
			"early_exit": early_exit,
			"half_day_status": half_day_status,
		}
	)
	attendance.flags.ignore_validate = ignore_validate
	attendance.insert()
	attendance.submit()


def create_ss_email_template():
	if not frappe.db.exists("Email Template", "Salary Slip"):
		ss_template = frappe.get_doc(
			{
				"doctype": "Email Template",
				"name": "Salary Slip",
				"response": "Test Salary Slip",
				"subject": "Test Salary Slip Email Template",
				"owner": frappe.session.user,
			}
		)
		ss_template.insert()


def clear_cache():
	for key in [
		HOLIDAYS_BETWEEN_DATES,
		LEAVE_TYPE_MAP,
		SALARY_COMPONENT_VALUES,
		TAX_COMPONENTS_BY_COMPANY,
	]:
		frappe.cache().delete_value(key)
