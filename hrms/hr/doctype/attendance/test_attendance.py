# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt

from datetime import datetime

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import (
	add_days,
	add_months,
	get_first_day,
	get_last_day,
	get_time,
	get_year_ending,
	get_year_start,
	getdate,
	nowdate,
)

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.attendance.attendance import (
	DuplicateAttendanceError,
	OverlappingShiftAttendanceError,
	get_events,
	get_unmarked_days,
	mark_attendance,
)
from hrms.hr.doctype.holiday_list_assignment.test_holiday_list_assignment import (
	assign_holiday_list,
	create_holiday_list_assignment,
)
from hrms.tests.test_utils import get_first_sunday


class TestAttendance(IntegrationTestCase):
	def setUp(self):
		from hrms.payroll.doctype.salary_slip.test_salary_slip import make_holiday_list

		from_date = get_year_start(add_months(getdate(), -1))
		to_date = get_year_ending(getdate())
		self.holiday_list = make_holiday_list(from_date=from_date, to_date=to_date)
		frappe.db.delete("Attendance")
		frappe.db.delete("Employee Checkin")

	def test_duplicate_attendance(self):
		employee = make_employee("test_duplicate_attendance@example.com", company="_Test Company")
		date = nowdate()

		mark_attendance(employee, date, "Present")
		attendance = frappe.get_doc(
			{
				"doctype": "Attendance",
				"employee": employee,
				"attendance_date": date,
				"status": "Absent",
				"company": "_Test Company",
			}
		)

		self.assertRaises(DuplicateAttendanceError, attendance.insert)

	def test_duplicate_attendance_with_shift(self):
		from hrms.hr.doctype.shift_type.test_shift_type import setup_shift_type

		employee = make_employee("test_duplicate_attendance@example.com", company="_Test Company")
		date = nowdate()

		shift_1 = setup_shift_type(shift_type="Shift 1", start_time="08:00:00", end_time="10:00:00")
		mark_attendance(employee, date, "Present", shift=shift_1.name)

		# attendance record with shift
		attendance = frappe.get_doc(
			{
				"doctype": "Attendance",
				"employee": employee,
				"attendance_date": date,
				"status": "Absent",
				"company": "_Test Company",
				"shift": shift_1.name,
			}
		)

		self.assertRaises(DuplicateAttendanceError, attendance.insert)

		# attendance record without any shift
		attendance = frappe.get_doc(
			{
				"doctype": "Attendance",
				"employee": employee,
				"attendance_date": date,
				"status": "Absent",
				"company": "_Test Company",
			}
		)

		self.assertRaises(DuplicateAttendanceError, attendance.insert)

	def test_overlapping_shift_attendance_validation(self):
		from hrms.hr.doctype.shift_type.test_shift_type import setup_shift_type

		employee = make_employee("test_overlap_attendance@example.com", company="_Test Company")
		date = nowdate()

		shift_1 = setup_shift_type(shift_type="Shift 1", start_time="08:00:00", end_time="10:00:00")
		shift_2 = setup_shift_type(shift_type="Shift 2", start_time="09:30:00", end_time="11:00:00")

		mark_attendance(employee, date, "Present", shift=shift_1.name)

		# attendance record with overlapping shift
		attendance = frappe.get_doc(
			{
				"doctype": "Attendance",
				"employee": employee,
				"attendance_date": date,
				"status": "Absent",
				"company": "_Test Company",
				"shift": shift_2.name,
			}
		)

		self.assertRaises(OverlappingShiftAttendanceError, attendance.insert)

	def test_allow_attendance_with_different_shifts(self):
		# allows attendance with 2 different non-overlapping shifts
		from hrms.hr.doctype.shift_type.test_shift_type import setup_shift_type

		employee = make_employee("test_duplicate_attendance@example.com", company="_Test Company")
		date = nowdate()

		shift_1 = setup_shift_type(shift_type="Shift 1", start_time="08:00:00", end_time="10:00:00")
		shift_2 = setup_shift_type(shift_type="Shift 2", start_time="11:00:00", end_time="12:00:00")

		mark_attendance(employee, date, "Present", shift_1.name)
		frappe.get_doc(
			{
				"doctype": "Attendance",
				"employee": employee,
				"attendance_date": date,
				"status": "Absent",
				"company": "_Test Company",
				"shift": shift_2.name,
			}
		).insert()

	def test_mark_absent(self):
		employee = make_employee("test_mark_absent@example.com")
		date = nowdate()

		attendance = mark_attendance(employee, date, "Absent")
		fetch_attendance = frappe.get_value(
			"Attendance", {"employee": employee, "attendance_date": date, "status": "Absent"}
		)
		self.assertEqual(attendance, fetch_attendance)

	def test_unmarked_days(self):
		first_sunday = get_first_sunday(self.holiday_list, for_date=get_last_day(add_months(getdate(), -1)))
		attendance_date = add_days(first_sunday, 1)

		employee = make_employee(
			"test_unmarked_days@example.com", date_of_joining=add_days(attendance_date, -1)
		)
		frappe.db.set_value("Employee", employee, "holiday_list", self.holiday_list)

		mark_attendance(employee, attendance_date, "Present")

		unmarked_days = get_unmarked_days(
			employee, get_first_day(attendance_date), get_last_day(attendance_date)
		)
		unmarked_days = [getdate(date) for date in unmarked_days]

		# attendance already marked for the day
		self.assertNotIn(attendance_date, unmarked_days)
		# attendance unmarked
		self.assertIn(getdate(add_days(attendance_date, 1)), unmarked_days)
		# holiday considered in unmarked days
		self.assertIn(first_sunday, unmarked_days)

	@assign_holiday_list("Salary Slip Test Holiday List", "_Test Company")
	def test_unmarked_days_excluding_holidays(self):
		first_sunday = get_first_sunday(self.holiday_list, for_date=get_last_day(add_months(getdate(), -1)))
		attendance_date = add_days(first_sunday, 1)

		employee = make_employee(
			"test_unmarked_days@example.com", date_of_joining=add_days(attendance_date, -1)
		)

		mark_attendance(employee, attendance_date, "Present")

		unmarked_days = get_unmarked_days(
			employee, get_first_day(attendance_date), get_last_day(attendance_date), exclude_holidays=True
		)
		unmarked_days = [getdate(date) for date in unmarked_days]

		# attendance already marked for the day
		self.assertNotIn(attendance_date, unmarked_days)
		# attendance unmarked
		self.assertIn(getdate(add_days(attendance_date, 1)), unmarked_days)
		# holidays not considered in unmarked days
		self.assertNotIn(first_sunday, unmarked_days)

	def test_unmarked_days_excluding_holidays_across_two_holiday_list_assignments(self):
		from hrms.payroll.doctype.salary_slip.test_salary_slip import make_holiday_list

		employee = make_employee("test_unmarked_days_exclude_holidays@example.com", company="_Test Company")
		start_date = get_first_day(getdate())
		mid_date = add_days(start_date, 15)
		end_date = get_last_day(getdate())
		holiday_list_1 = make_holiday_list(
			"First Holiday List", from_date=start_date, to_date=add_days(mid_date, -1)
		)
		holiday_list_2 = make_holiday_list("Second Holiday List", from_date=mid_date, to_date=end_date)
		create_holiday_list_assignment("Employee", employee, holiday_list=holiday_list_1)
		create_holiday_list_assignment("Employee", employee, holiday_list=holiday_list_2)

		unmarked_days = get_unmarked_days(employee, start_date, end_date, exclude_holidays=True)
		unmarked_days = [getdate(date) for date in unmarked_days]
		sunday_in_holiday_list_1 = get_first_sunday(holiday_list=holiday_list_1, for_date=start_date)
		sunday_in_holiday_list_2 = get_first_sunday(holiday_list=holiday_list_2, for_date=end_date)

		self.assertNotIn(sunday_in_holiday_list_1, unmarked_days)
		self.assertNotIn(sunday_in_holiday_list_2, unmarked_days)

	def test_unmarked_days_as_per_joining_and_relieving_dates(self):
		first_sunday = get_first_sunday(self.holiday_list, for_date=get_last_day(add_months(getdate(), -1)))
		date = add_days(first_sunday, 1)

		doj = add_days(date, 1)
		relieving_date = add_days(date, 5)
		employee = make_employee(
			"test_unmarked_days_as_per_doj@example.com", date_of_joining=doj, relieving_date=relieving_date
		)

		frappe.db.set_value("Employee", employee, "holiday_list", self.holiday_list)

		attendance_date = add_days(date, 2)
		mark_attendance(employee, attendance_date, "Present")

		unmarked_days = get_unmarked_days(
			employee, get_first_day(attendance_date), get_last_day(attendance_date)
		)
		unmarked_days = [getdate(date) for date in unmarked_days]

		# attendance already marked for the day
		self.assertNotIn(attendance_date, unmarked_days)
		# date before doj not in unmarked days
		self.assertNotIn(add_days(doj, -1), unmarked_days)
		# date after relieving not in unmarked days
		self.assertNotIn(add_days(relieving_date, 1), unmarked_days)

	def test_duplicate_attendance_when_created_from_checkins_and_tool(self):
		from hrms.hr.doctype.employee_checkin.test_employee_checkin import make_checkin
		from hrms.hr.doctype.shift_type.test_shift_type import setup_shift_type

		shift = setup_shift_type(shift_type="Shift 1", start_time="08:00:00", end_time="17:00:00")
		employee = make_employee(
			"test_duplicate@attendance.com", company="_Test Company", default_shift=shift.name
		)
		mark_attendance(employee, getdate(), "Half Day", shift=shift.name, half_day_status="Absent")
		make_checkin(employee, datetime.combine(getdate(), get_time("14:00:00")))
		shift.process_auto_attendance()

		attendances = frappe.get_all(
			"Attendance",
			filters={
				"employee": employee,
				"attendance_date": getdate(),
			},
		)
		self.assertEqual(len(attendances), 1)

	def test_get_events_returns_attendance(self):
		employee = make_employee("calendar.user@example.com", company="_Test Company")

		attendance_name = mark_attendance(employee, getdate(), status="Present")
		attendance = frappe.get_value("Attendance", attendance_name, "status")

		self.assertEqual(attendance, "Present")

		frappe.set_user("calendar.user@example.com")
		try:
			events = get_events(start=getdate(), end=getdate())
		finally:
			frappe.set_user("Administrator")

		self.assertTrue(events)
		attendance_events = [e for e in events if e.get("doctype") == "Attendance"]
		self.assertTrue(attendance_events)
		self.assertEqual(attendance_events[0].get("status"), "Present")
		self.assertEqual(
			attendance_events[0].get("employee_name"),
			frappe.db.get_value("Employee", employee, "employee_name"),
		)
		self.assertEqual(attendance_events[0].get("attendance_date"), getdate())

	def tearDown(self):
		frappe.db.rollback()
