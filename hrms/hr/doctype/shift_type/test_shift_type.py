# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
from datetime import datetime, timedelta

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import (
	add_days,
	get_datetime,
	get_time,
	get_year_ending,
	get_year_start,
	getdate,
	now_datetime,
)

from erpnext.setup.doctype.employee.test_employee import make_employee
from erpnext.setup.doctype.holiday_list.test_holiday_list import set_holiday_list

from hrms.hr.doctype.leave_application.test_leave_application import get_first_sunday
from hrms.hr.doctype.shift_type.shift_type import update_last_sync_of_checkin
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_holiday_list
from hrms.tests.test_utils import add_date_to_holiday_list


class TestShiftType(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("Shift Type")
		frappe.db.delete("Shift Assignment")
		frappe.db.delete("Employee Checkin")
		frappe.db.delete("Attendance")

		from_date = get_year_start(getdate())
		to_date = get_year_ending(getdate())
		self.holiday_list = make_holiday_list(from_date=from_date, to_date=to_date)

	def test_auto_update_last_sync_of_checkin_for_single_day_shift(self):
		shift_type = setup_shift_type()
		shift_type.last_sync_of_checkin = None
		shift_type.auto_update_last_sync = 1
		shift_type.save()

		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")
		date = getdate()
		make_shift_assignment(shift_type.name, employee, date)

		# case 1: last sync updates from none to shift end after the shift end time
		frappe.flags.current_datetime = datetime.combine(getdate(), get_time("14:00:00"))
		update_last_sync_of_checkin()
		shift_type.reload()
		# last sync should be updated to 13:00:00
		self.assertEqual(shift_type.last_sync_of_checkin, datetime.combine(getdate(), get_time("13:01:00")))

		# case 2: last sync doesn't update in the middle of the shift
		frappe.flags.current_datetime = add_days(datetime.combine(getdate(), get_time("12:00:00")), 1)
		update_last_sync_of_checkin()
		shift_type.reload()
		self.assertEqual(shift_type.last_sync_of_checkin, datetime.combine(getdate(), get_time("13:01:00")))

	def test_auto_update_last_sync_of_checkin_for_shifts_spanning_two_days_due_to_buffer(self):
		shift_type = setup_shift_type(
			shift_type="_Test Extra Buffer Shift",
			start_time="11:00:00",
			end_time="19:00:00",
			allow_check_out_after_shift_end_time=360,
		)
		shift_type.last_sync_of_checkin = None
		shift_type.auto_update_last_sync = 1
		shift_type.save()

		employee = make_employee("test_employee_checkin3@example.com", company="_Test Company")
		date = add_days(getdate(), -4)
		make_shift_assignment(shift_type.name, employee, date)

		# case 1: last sync updates from none to shift end after the shift end time
		frappe.flags.current_datetime = datetime.combine(getdate(), get_time("02:00:00"))
		update_last_sync_of_checkin()
		shift_type.reload()
		# last sync should be updated to 01:01:00
		self.assertEqual(shift_type.last_sync_of_checkin, datetime.combine(getdate(), get_time("01:01:00")))

		# case 2: last sync doesn't update in the middle of the shift
		frappe.flags.current_datetime = datetime.combine(getdate(), get_time("19:00:00"))
		update_last_sync_of_checkin()
		shift_type.reload()
		self.assertEqual(shift_type.last_sync_of_checkin, datetime.combine(getdate(), get_time("01:01:00")))

	def test_auto_update_last_sync_of_checkin_for_two_day_shift(self):
		shift_type = setup_shift_type(
			shift_type="_Test Night Shift", start_time="22:00:00", end_time="06:00:00"
		)
		shift_type.last_sync_of_checkin = None
		shift_type.auto_update_last_sync = 1
		shift_type.save()

		employee = make_employee("test_employee_checkin2@example.com", company="_Test Company")
		date = add_days(getdate(), -4)
		make_shift_assignment(shift_type.name, employee, date)

		# case 1: last sync updates from none to shift end after the shift end time
		frappe.flags.current_datetime = datetime.combine(getdate(), get_time("08:00:00"))
		update_last_sync_of_checkin()
		shift_type.reload()
		# last sync should be updated to 07:01:00
		self.assertEqual(shift_type.last_sync_of_checkin, datetime.combine(getdate(), get_time("07:01:00")))

		# case 2: last sync doesn't update in the middle of the shift
		frappe.flags.current_datetime = add_days(datetime.combine(getdate(), get_time("01:00:00")), 1)
		update_last_sync_of_checkin()
		shift_type.reload()
		self.assertEqual(shift_type.last_sync_of_checkin, datetime.combine(getdate(), get_time("07:01:00")))

	def test_auto_update_last_sync_of_checkin_when_when_job_runs_on_the_next_day(self):
		shift_type = setup_shift_type(shift_type="Test Long Shift", start_time="9:00:00", end_time="18:00:00")
		shift_type.allow_check_out_after_shift_end_time = 330
		shift_type.last_sync_of_checkin = None
		shift_type.auto_update_last_sync = 1
		shift_type.save()

		frappe.flags.current_datetime = datetime.combine(add_days(getdate(), 1), get_time("00:01:00"))
		update_last_sync_of_checkin()

		shift_type.reload()

		self.assertEqual(shift_type.last_sync_of_checkin, datetime.combine(getdate(), get_time("23:31:00")))

	def test_mark_attendance(self):
		from hrms.hr.doctype.employee_checkin.test_employee_checkin import make_checkin

		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")

		shift_type = setup_shift_type()
		date = getdate()
		make_shift_assignment(shift_type.name, employee, date)

		timestamp = datetime.combine(date, get_time("08:00:00"))
		log_in = make_checkin(employee, timestamp)
		self.assertEqual(log_in.shift, shift_type.name)

		timestamp = datetime.combine(date, get_time("12:00:00"))
		log_out = make_checkin(employee, timestamp)
		self.assertEqual(log_out.shift, shift_type.name)

		shift_type.process_auto_attendance()

		attendance = frappe.db.get_value(
			"Attendance", {"employee": employee, "shift": shift_type.name}, "status"
		)
		self.assertEqual(attendance, "Present")

	def test_mark_attendance_with_different_shift_start_time(self):
		"""Tests whether attendance is marked correctly if shift configuration is changed midway"""
		from hrms.hr.doctype.employee_checkin.test_employee_checkin import make_checkin

		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")

		shift_type = setup_shift_type(shift_type="Test Shift Start")
		date = getdate()
		make_shift_assignment(shift_type.name, employee, date)

		timestamp = datetime.combine(date, get_time("08:00:00"))
		# log in
		make_checkin(employee, timestamp)

		# change config before adding OUT log
		shift_type.begin_check_in_before_shift_start_time = 120
		shift_type.save()

		timestamp = datetime.combine(date, get_time("12:00:00"))
		# log out
		make_checkin(employee, timestamp)

		shift_type.process_auto_attendance()

		attendance = frappe.db.get_value(
			"Attendance", {"employee": employee, "shift": shift_type.name}, "status"
		)
		self.assertEqual(attendance, "Present")

	def test_attendance_date_for_different_start_and_actual_start_date(self):
		from hrms.hr.doctype.employee_checkin.test_employee_checkin import make_checkin

		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")
		shift_type = setup_shift_type(shift_type="Midnight Shift", start_time="00:30:00", end_time="10:00:00")

		date = getdate()
		make_shift_assignment(shift_type.name, employee, date, date)

		timestamp = datetime.combine(date, get_time("00:30:00"))
		# log in
		make_checkin(employee, timestamp)

		timestamp = datetime.combine(date, get_time("10:00:00"))
		# log out
		make_checkin(employee, timestamp)

		shift_type.process_auto_attendance()

		# even though actual start time starts on the prev date,
		# attendance date should be the current date (start date of the shift)
		attendance = frappe.db.get_value(
			"Attendance",
			{"shift": shift_type.name},
			["attendance_date", "status"],
			as_dict=True,
		)
		self.assertEqual(attendance.status, "Present")
		self.assertEqual(attendance.attendance_date, date)

	def test_entry_and_exit_grace(self):
		from hrms.hr.doctype.employee_checkin.test_employee_checkin import make_checkin

		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")

		# doesn't mark late entry until 60 mins after shift start i.e. till 9
		# doesn't mark late entry until 60 mins before shift end i.e. 11
		shift_type = setup_shift_type(
			enable_late_entry_marking=1,
			enable_early_exit_marking=1,
			late_entry_grace_period=60,
			early_exit_grace_period=60,
		)
		date = getdate()
		make_shift_assignment(shift_type.name, employee, date)

		timestamp = datetime.combine(date, get_time("09:30:00"))
		log_in = make_checkin(employee, timestamp)
		self.assertEqual(log_in.shift, shift_type.name)

		timestamp = datetime.combine(date, get_time("10:30:00"))
		log_out = make_checkin(employee, timestamp)
		self.assertEqual(log_out.shift, shift_type.name)

		shift_type.process_auto_attendance()

		attendance = frappe.db.get_value(
			"Attendance",
			{"shift": shift_type.name, "employee": employee},
			["status", "name", "late_entry", "early_exit"],
			as_dict=True,
		)
		self.assertEqual(attendance.status, "Present")
		self.assertEqual(attendance.late_entry, 1)
		self.assertEqual(attendance.early_exit, 1)

	def test_working_hours_threshold_for_half_day(self):
		from hrms.hr.doctype.employee_checkin.test_employee_checkin import make_checkin

		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")
		shift_type = setup_shift_type(shift_type="Half Day Test", working_hours_threshold_for_half_day=2)
		date = getdate()
		make_shift_assignment(shift_type.name, employee, date)

		timestamp = datetime.combine(date, get_time("08:00:00"))
		log_in = make_checkin(employee, timestamp)
		self.assertEqual(log_in.shift, shift_type.name)

		timestamp = datetime.combine(date, get_time("09:30:00"))
		log_out = make_checkin(employee, timestamp)
		self.assertEqual(log_out.shift, shift_type.name)

		shift_type.process_auto_attendance()

		attendance = frappe.db.get_value(
			"Attendance", {"shift": shift_type.name}, ["status", "working_hours"], as_dict=True
		)
		self.assertEqual(attendance.status, "Half Day")
		self.assertEqual(attendance.working_hours, 1.5)

	def test_working_hours_threshold_for_absent(self):
		from hrms.hr.doctype.employee_checkin.test_employee_checkin import make_checkin

		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")
		shift_type = setup_shift_type(shift_type="Absent Test", working_hours_threshold_for_absent=2)
		date = getdate()
		make_shift_assignment(shift_type.name, employee, date)

		timestamp = datetime.combine(date, get_time("08:00:00"))
		log_in = make_checkin(employee, timestamp)
		self.assertEqual(log_in.shift, shift_type.name)

		timestamp = datetime.combine(date, get_time("09:30:00"))
		log_out = make_checkin(employee, timestamp)
		self.assertEqual(log_out.shift, shift_type.name)

		shift_type.process_auto_attendance()

		attendance = frappe.db.get_value(
			"Attendance", {"shift": shift_type.name}, ["status", "working_hours"], as_dict=True
		)
		self.assertEqual(attendance.status, "Absent")
		self.assertEqual(attendance.working_hours, 1.5)

	def test_working_hours_threshold_for_absent_and_half_day_1(self):
		# considers half day over absent
		from hrms.hr.doctype.employee_checkin.test_employee_checkin import make_checkin

		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")
		shift_type = setup_shift_type(
			shift_type="Half Day + Absent Test",
			working_hours_threshold_for_half_day=2,
			working_hours_threshold_for_absent=1,
		)
		date = getdate()
		make_shift_assignment(shift_type.name, employee, date)

		timestamp = datetime.combine(date, get_time("08:00:00"))
		log_in = make_checkin(employee, timestamp)
		self.assertEqual(log_in.shift, shift_type.name)

		timestamp = datetime.combine(date, get_time("09:30:00"))
		log_out = make_checkin(employee, timestamp)
		self.assertEqual(log_out.shift, shift_type.name)

		shift_type.process_auto_attendance()

		attendance = frappe.db.get_value(
			"Attendance", {"shift": shift_type.name}, ["status", "working_hours"], as_dict=True
		)
		self.assertEqual(attendance.status, "Half Day")
		self.assertEqual(attendance.working_hours, 1.5)

	def test_working_hours_threshold_for_absent_and_half_day_2(self):
		# considers absent over half day
		from hrms.hr.doctype.employee_checkin.test_employee_checkin import make_checkin

		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")
		shift_type = setup_shift_type(
			shift_type="Half Day + Absent Test",
			working_hours_threshold_for_half_day=2,
			working_hours_threshold_for_absent=1,
		)
		date = getdate()
		make_shift_assignment(shift_type.name, employee, date)

		timestamp = datetime.combine(date, get_time("08:00:00"))
		log_in = make_checkin(employee, timestamp)
		self.assertEqual(log_in.shift, shift_type.name)

		timestamp = datetime.combine(date, get_time("08:45:00"))
		log_out = make_checkin(employee, timestamp)
		self.assertEqual(log_out.shift, shift_type.name)

		shift_type.process_auto_attendance()

		attendance = frappe.db.get_value("Attendance", {"shift": shift_type.name}, "status")
		self.assertEqual(attendance, "Absent")

	@set_holiday_list("Salary Slip Test Holiday List", "_Test Company")
	def test_mark_auto_attendance_on_holiday_enabled(self):
		from hrms.hr.doctype.employee_checkin.test_employee_checkin import make_checkin

		# add current date as holiday
		date = getdate()
		add_date_to_holiday_list(date, self.holiday_list)

		shift_type = setup_shift_type(shift_type="Test Holiday Shift", mark_auto_attendance_on_holidays=True)
		shift_type.holiday_list = None
		shift_type.save()

		employee = make_employee(
			"test_shift_with_holiday@example.com", default_shift=shift_type.name, company="_Test Company"
		)

		# make logs
		timestamp = datetime.combine(date, get_time("08:00:00"))
		make_checkin(employee, timestamp)
		timestamp = datetime.combine(date, get_time("12:00:00"))
		make_checkin(employee, timestamp)

		shift_type.process_auto_attendance()

		attendance = frappe.db.get_value(
			"Attendance", {"employee": employee, "attendance_date": date}, "status"
		)
		self.assertEqual(attendance, "Present")

	@set_holiday_list("Salary Slip Test Holiday List", "_Test Company")
	def test_mark_auto_attendance_on_holiday_disabled(self):
		from hrms.hr.doctype.employee_checkin.test_employee_checkin import make_checkin

		# add current date as holiday
		date = getdate()
		add_date_to_holiday_list(date, self.holiday_list)

		shift_type = setup_shift_type(shift_type="Test Holiday Shift", mark_auto_attendance_on_holidays=False)
		shift_type.holiday_list = None
		shift_type.save()

		employee = make_employee(
			"test_shift_with_holiday@example.com", default_shift=shift_type.name, company="_Test Company"
		)

		# make logs
		timestamp = datetime.combine(date, get_time("08:00:00"))
		make_checkin(employee, timestamp)
		timestamp = datetime.combine(date, get_time("12:00:00"))
		make_checkin(employee, timestamp)

		shift_type.process_auto_attendance()

		attendance = frappe.db.get_value(
			"Attendance", {"employee": employee, "attendance_date": date}, "status"
		)
		self.assertIsNone(attendance)

	def test_mark_absent_for_dates_with_no_attendance(self):
		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")
		today = getdate()
		shift_type = setup_shift_type(
			shift_type="Test Absent with no Attendance",
			process_attendance_after=add_days(today, -6),
			last_sync_of_checkin=f"{today} 15:00:00",
		)
		# single day assignment
		date1 = add_days(today, -5)
		make_shift_assignment(shift_type.name, employee, date1, date1)

		# assignment without end date
		date2 = add_days(today, -4)
		make_shift_assignment(shift_type.name, employee, date2)

		shift_type.process_auto_attendance()
		yesterday = add_days(today, -1)

		# absentees are auto-marked one day after shift actual end to wait for any manual attendance records
		# so all days should be marked as absent except today
		absent_records = frappe.get_all(
			"Attendance",
			{
				"attendance_date": ["between", [date1, yesterday]],
				"employee": employee,
				"status": "Absent",
			},
		)
		self.assertEqual(len(absent_records), 5)
		todays_attendance = frappe.db.get_value(
			"Attendance", {"attendance_date": today, "employee": employee}
		)
		self.assertIsNone(todays_attendance)

	def test_mark_absent_for_dates_with_no_attendance_for_midnight_shift(self):
		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")
		today = getdate()
		shift_type = setup_shift_type(
			shift_type="Test Absent with no Attendance",
			start_time="15:00:00",
			end_time="23:30:00",
			process_attendance_after=add_days(today, -8),
			allow_check_out_after_shift_end_time=120,
			last_sync_of_checkin=f"{today} 15:00:00",
		)
		# single day assignment
		date1 = add_days(today, -7)
		make_shift_assignment(shift_type.name, employee, date1, date1)

		# assignment after a gap
		date2 = add_days(today, -5)
		make_shift_assignment(shift_type.name, employee, date2, date2)

		# assignment without end date
		date3 = add_days(today, -3)
		make_shift_assignment(shift_type.name, employee, date3)

		shift_type.process_auto_attendance()
		absent_records = frappe.get_all(
			"Attendance",
			fields=["name", "employee", "attendance_date", "status", "shift"],
			filters={
				"attendance_date": ["between", [date1, today]],
				"employee": employee,
				"status": "Absent",
			},
		)

		self.assertEqual(len(absent_records), 5)
		# absent for first assignment
		self.assertEqual(
			frappe.db.get_value(
				"Attendance",
				{"attendance_date": date1, "shift": shift_type.name, "employee": employee},
				"status",
			),
			"Absent",
		)
		# no attendance for day after first assignment
		self.assertIsNone(
			frappe.db.get_value(
				"Attendance",
				{"attendance_date": add_days(date1, 1), "shift": shift_type.name, "employee": employee},
			)
		)
		# absent for second assignment
		self.assertEqual(
			frappe.db.get_value(
				"Attendance",
				{"attendance_date": date2, "shift": shift_type.name, "employee": employee},
				"status",
			),
			"Absent",
		)
		# no attendance for day after second assignment
		self.assertIsNone(
			frappe.db.get_value(
				"Attendance",
				{"attendance_date": add_days(date2, 1), "shift": shift_type.name, "employee": employee},
			)
		)
		# absent for third assignment
		self.assertEqual(
			frappe.db.get_value(
				"Attendance",
				{"attendance_date": date3, "shift": shift_type.name, "employee": employee},
				"status",
			),
			"Absent",
		)
		self.assertEqual(
			frappe.db.get_value(
				"Attendance",
				{"attendance_date": add_days(date3, 1), "shift": shift_type.name, "employee": employee},
				"status",
			),
			"Absent",
		)

	def test_do_not_mark_absent_before_shift_actual_end_time(self):
		from hrms.hr.doctype.employee_checkin.test_employee_checkin import make_checkin

		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")
		today = getdate()
		yesterday = add_days(today, -1)

		# shift 1
		shift_1 = setup_shift_type(shift_type="Morning", start_time="07:00:00", end_time="12:30:00")
		make_shift_assignment(shift_1.name, employee, add_days(yesterday, -1), yesterday)

		# shift 2
		shift_2 = setup_shift_type(shift_type="Afternoon", start_time="09:30:00", end_time="18:00:00")
		make_shift_assignment(shift_2.name, employee, today, add_days(today, 1))

		# update last sync of checkin for shift 2
		shift_2.process_attendance_after = add_days(today, -2)
		shift_2.last_sync_of_checkin = datetime.combine(today, get_time("09:01:00"))
		shift_2.save()
		shift_2.process_auto_attendance()

		self.assertIsNone(frappe.db.get_value("Attendance", {"attendance_date": today, "employee": employee}))

	def test_do_not_mark_absent_before_shift_actual_end_time_for_midnight_shift(self):
		"""
		Tests employee is not marked absent for a shift spanning 2 days
		before its actual end time
		"""
		from hrms.hr.doctype.employee_checkin.test_employee_checkin import make_checkin

		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")
		curr_date = getdate()

		# this shift's valid checkout period (+60 mins) will be till 00:30:00 today, so it goes beyond a day
		shift_type = setup_shift_type(shift_type="Test Absent", start_time="15:00:00", end_time="23:30:00")
		shift_type.last_sync_of_checkin = datetime.combine(curr_date, get_time("00:30:00"))
		shift_type.save()

		# assign shift for yesterday, actual end time is today at 00:30:00
		prev_date = add_days(getdate(), -1)
		make_shift_assignment(shift_type.name, employee, prev_date)

		# make logs
		timestamp = datetime.combine(prev_date, get_time("15:00:00"))
		make_checkin(employee, timestamp)
		timestamp = datetime.combine(prev_date, get_time("23:30:00"))
		make_checkin(employee, timestamp)

		# last sync of checkin is 00:30:00 and the checkin logs are not applicable for attendance yet
		# so it should not mark the employee as absent either
		shift_type.process_auto_attendance()
		attendance = frappe.db.get_value(
			"Attendance", {"attendance_date": prev_date, "employee": employee}, "status"
		)
		self.assertIsNone(attendance)

		# update last sync
		shift_type.last_sync_of_checkin = datetime.combine(curr_date, get_time("01:00:00"))
		shift_type.save()
		shift_type.process_auto_attendance()
		# employee marked present considering checkins
		attendance = frappe.db.get_value(
			"Attendance", {"attendance_date": prev_date, "employee": employee}, "status"
		)
		self.assertEqual(attendance, "Present")

	@set_holiday_list("Salary Slip Test Holiday List", "_Test Company")
	def test_skip_marking_absent_on_a_holiday(self):
		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")
		shift_type = setup_shift_type(shift_type="Test Absent with no Attendance")
		shift_type.holiday_list = None
		shift_type.save()

		# should not mark any attendance if no shift assignment is created
		shift_type.process_auto_attendance()
		attendance = frappe.db.get_value("Attendance", {"employee": employee}, "status")
		self.assertIsNone(attendance)

		first_sunday = get_first_sunday(self.holiday_list, for_date=getdate())
		make_shift_assignment(shift_type.name, employee, first_sunday)

		shift_type.process_auto_attendance()

		attendance = frappe.db.get_value(
			"Attendance",
			{"attendance_date": first_sunday, "employee": employee},
		)
		self.assertIsNone(attendance)

	def test_skip_absent_marking_for_a_fallback_default_shift(self):
		"""
		Tests if an employee is not marked absent for default shift
		when they have a valid shift assignment of another type.
		Assigned shift takes precedence over default shift
		"""
		from hrms.hr.doctype.employee_checkin.test_employee_checkin import make_checkin

		default_shift = setup_shift_type()
		employee = make_employee(
			"test_employee_checkin_default@example.com",
			company="_Test Company",
			default_shift=default_shift.name,
		)

		assigned_shift = setup_shift_type(shift_type="Test Absent with no Attendance")
		date = getdate()
		make_shift_assignment(assigned_shift.name, employee, date)

		timestamp = datetime.combine(date, get_time("08:00:00"))
		# log in
		make_checkin(employee, timestamp)

		timestamp = datetime.combine(date, get_time("10:00:00"))
		# log out
		make_checkin(employee, timestamp)

		default_shift.process_auto_attendance()
		attendance = frappe.db.get_value(
			"Attendance", {"employee": employee, "shift": default_shift.name}, "status"
		)
		self.assertIsNone(attendance)

		assigned_shift.process_auto_attendance()
		attendance = frappe.db.get_value(
			"Attendance", {"employee": employee, "shift": assigned_shift.name}, "status"
		)
		self.assertEqual(attendance, "Present")

	def test_skip_absent_marking_for_inactive_employee(self):
		from hrms.hr.doctype.employee_checkin.test_employee_checkin import make_checkin

		shift = setup_shift_type()
		employee = make_employee("test_inactive_employee@example.com", company="_Test Company")
		date = getdate()
		make_shift_assignment(shift.name, employee, date)

		# mark employee as Inactive
		frappe.db.set_value("Employee", employee, "status", "Inactive")

		shift.process_auto_attendance()
		attendance = frappe.db.get_value("Attendance", {"employee": employee}, "status")
		self.assertIsNone(attendance)

	def test_get_start_and_end_dates(self):
		date = getdate()

		doj = add_days(date, -30)
		relieving_date = add_days(date, -5)
		employee = make_employee(
			"test_employee_dates@example.com",
			company="_Test Company",
			date_of_joining=doj,
			relieving_date=relieving_date,
		)
		shift_type = setup_shift_type(
			shift_type="Test Absent with no Attendance", process_attendance_after=add_days(doj, 2)
		)

		make_shift_assignment(shift_type.name, employee, add_days(date, -25))

		shift_type.process_auto_attendance()

		# should not mark absent before shift assignment/process attendance after date
		attendance = frappe.db.get_value("Attendance", {"attendance_date": doj, "employee": employee}, "name")
		self.assertIsNone(attendance)

		# mark absent on Relieving Date
		attendance = frappe.db.get_value(
			"Attendance", {"attendance_date": relieving_date, "employee": employee}, "status"
		)
		self.assertEqual(attendance, "Absent")

		# should not mark absent after Relieving Date
		attendance = frappe.db.get_value(
			"Attendance", {"attendance_date": add_days(relieving_date, 1), "employee": employee}, "name"
		)
		self.assertIsNone(attendance)

	def test_skip_auto_attendance_for_duplicate_record(self):
		# Skip auto attendance in case of duplicate attendance record
		from hrms.hr.doctype.attendance.attendance import mark_attendance
		from hrms.hr.doctype.employee_checkin.test_employee_checkin import make_checkin

		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")

		shift_type = setup_shift_type()
		date = getdate()

		# mark attendance
		mark_attendance(employee, date, "Present")
		make_shift_assignment(shift_type.name, employee, date)

		timestamp = datetime.combine(date, get_time("08:00:00"))
		log_in = make_checkin(employee, timestamp)
		self.assertEqual(log_in.shift, shift_type.name)

		timestamp = datetime.combine(date, get_time("12:00:00"))
		log_out = make_checkin(employee, timestamp)
		self.assertEqual(log_out.shift, shift_type.name)

		# auto attendance should skip marking
		shift_type.process_auto_attendance()

		log_in.reload()
		log_out.reload()
		self.assertEqual(log_in.skip_auto_attendance, 1)
		self.assertEqual(log_out.skip_auto_attendance, 1)

	def test_skip_auto_attendance_for_overlapping_shift(self):
		# Skip auto attendance in case of overlapping shift attendance record
		# this case won't occur in case of shift assignment, since it will not allow overlapping shifts to be assigned
		# can happen if manual attendance records are created
		from hrms.hr.doctype.attendance.attendance import mark_attendance
		from hrms.hr.doctype.employee_checkin.test_employee_checkin import make_checkin

		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")
		shift_1 = setup_shift_type(shift_type="Shift 1", start_time="08:00:00", end_time="10:00:00")
		shift_2 = setup_shift_type(shift_type="Shift 2", start_time="09:30:00", end_time="11:00:00")

		date = getdate()

		# mark attendance
		mark_attendance(employee, date, "Present", shift=shift_1.name)
		make_shift_assignment(shift_2.name, employee, date)

		timestamp = datetime.combine(date, get_time("09:30:00"))
		log_in = make_checkin(employee, timestamp)
		self.assertEqual(log_in.shift, shift_2.name)

		timestamp = datetime.combine(date, get_time("11:00:00"))
		log_out = make_checkin(employee, timestamp)
		self.assertEqual(log_out.shift, shift_2.name)

		# auto attendance should be skipped for shift 2
		# since it is already marked for overlapping shift 1
		shift_2.process_auto_attendance()

		log_in.reload()
		log_out.reload()
		self.assertEqual(log_in.skip_auto_attendance, 1)
		self.assertEqual(log_out.skip_auto_attendance, 1)

	def test_mark_attendance_for_default_shift_when_shift_assignment_is_not_overlapping(self):
		shift_1 = setup_shift_type(shift_type="Deafult Shift", start_time="08:00:00", end_time="12:00:00")
		shift_2 = setup_shift_type(shift_type="Not Default Shift", start_time="10:00:00", end_time="18:00:00")
		employee = make_employee(
			"test_employee_attendance@example.com", company="_Test Company", default_shift=shift_1.name
		)
		shift_assigned_date = add_days(getdate(), +1)
		make_shift_assignment(shift_2.name, employee, shift_assigned_date)
		from hrms.hr.doctype.attendance.attendance import mark_attendance

		mark_attendance(employee, add_days(getdate(), -1), "Present", shift=shift_1.name)
		shift_1.process_auto_attendance()
		self.assertEqual(
			frappe.db.get_value(
				"Attendance",
				{"employee": employee, "attendance_date": getdate(), "shift": shift_1.name},
				"status",
			),
			"Absent",
		)

	def test_validation_for_unlinked_logs_before_changing_important_shift_configuration(self):
		# the important shift configuration is start time, it is used to sort logs chronologically
		shift = setup_shift_type(shift_type="Test Shift", start_time="10:00:00", end_time="18:00:00")
		employee = make_employee(
			"test_employee4_attendance@example.com", company="_Test Company", default_shift=shift.name
		)

		from hrms.hr.doctype.employee_checkin.test_employee_checkin import make_checkin

		in_time = datetime.combine(getdate(), get_time("10:00:00"))
		check_in = make_checkin(employee, in_time)
		check_in.fetch_shift()
		# Case 1: raise valdiation error if shift time is being changed and checkin logs exists
		shift.start_time = get_time("10:15:00")
		self.assertRaises(frappe.ValidationError, shift.save)

		# don't raise validation error if something else is being changed
		# even if checkin logs exists, it's probably fine
		shift.reload()
		shift.begin_check_in_before_shift_start_time = 120
		shift.save()
		self.assertEqual(
			frappe.get_value("Shift Type", shift.name, "begin_check_in_before_shift_start_time"), 120
		)
		out_time = datetime.combine(getdate(), get_time("18:00:00"))
		check_out = make_checkin(employee, out_time)
		check_out.fetch_shift()
		shift.process_auto_attendance()

		# Case 2: allow shift time to change if no unlinked logs exist
		shift.start_time = get_time("10:15:00")
		shift.save()
		self.assertEqual(
			get_time(frappe.get_value("Shift Type", shift.name, "start_time")), get_time("10:15:00")
		)

	def test_circular_shift_times(self):
		# single day shift
		shift_type = frappe.get_doc(
			{
				"doctype": "Shift Type",
				"__newname": "Test Shift Validation",
				"start_time": "09:00:00",
				"end_time": "18:00:00",
				"enable_auto_attendance": 1,
				"determine_check_in_and_check_out": "Alternating entries as IN and OUT during the same shift",
				"working_hours_calculation_based_on": "First Check-in and Last Check-out",
				"begin_check_in_before_shift_start_time": 500,
				"allow_check_out_after_shift_end_time": 500,
				"process_attendance_after": add_days(getdate(), -2),
				"last_sync_of_checkin": now_datetime() + timedelta(days=1),
			}
		)

		self.assertRaises(frappe.ValidationError, shift_type.save)

		# two day shift
		shift_type = frappe.get_doc(
			{
				"doctype": "Shift Type",
				"__newname": "Test Shift Validation",
				"start_time": "18:00:00",
				"end_time": "03:00:00",
				"enable_auto_attendance": 1,
				"determine_check_in_and_check_out": "Alternating entries as IN and OUT during the same shift",
				"working_hours_calculation_based_on": "First Check-in and Last Check-out",
				"begin_check_in_before_shift_start_time": 500,
				"allow_check_out_after_shift_end_time": 500,
				"process_attendance_after": add_days(getdate(), -2),
				"last_sync_of_checkin": now_datetime() + timedelta(days=1),
			}
		)
		self.assertRaises(frappe.ValidationError, shift_type.save)

	def test_bg_job_creation_for_large_checkins(self):
		shift = setup_shift_type(shift_type="Test Shift", start_time="10:00:00", end_time="18:00:00")
		frappe.flags.test_bg_job = True
		shift.process_auto_attendance(is_manually_triggered=True)
		job = frappe.get_all("RQ Job", {"job_id": f"process_auto_attendance_{shift.name}"})
		self.assertTrue(job)

	def test_precision_for_working_hours_threshold(self):
		shift = setup_shift_type(
			start_time="10:00:00",
			end_time="18:00:00",
			working_hours_threshold_for_half_day=4.75,
			working_hours_threshold_for_absent=1.25,
		)
		employee = make_employee(
			"test_working_hours@example.com", company="_Test Company", default_shift=shift.name
		)
		from hrms.hr.doctype.employee_checkin.test_employee_checkin import make_checkin

		in_time = datetime.combine(getdate(), get_time("10:00:00"))
		make_checkin(employee, in_time)

		# checked out before completing absent hours threshold
		out_time = datetime.combine(getdate(), get_time("11:14:00"))
		check_out = make_checkin(employee, out_time)
		shift.process_auto_attendance()
		attendance = frappe.get_doc(
			"Attendance", {"employee": employee, "shift": shift.name, "attendance_date": getdate()}
		)
		self.assertEqual(attendance.status, "Absent")
		attendance.cancel()

		# barely passed absent hour threshold
		check_out.time = datetime.combine(getdate(), get_time("11:15:00"))
		check_out.save()
		shift.process_auto_attendance()
		attendance = frappe.get_doc(
			"Attendance", {"employee": employee, "shift": shift.name, "attendance_date": getdate()}
		)
		self.assertEqual(attendance.status, "Half Day")
		self.assertEqual(attendance.working_hours, 1.25)
		attendance.cancel()

		# barely passed half day hour threshold
		check_out.time = datetime.combine(getdate(), get_time("14:45:00"))
		check_out.save()
		shift.process_auto_attendance()
		attendance = frappe.get_doc(
			"Attendance", {"employee": employee, "shift": shift.name, "attendance_date": getdate()}
		)
		self.assertEqual(attendance.status, "Present")
		self.assertEqual(attendance.working_hours, 4.75)


def setup_shift_type(**args):
	args = frappe._dict(args)
	date = getdate()
	if not frappe.db.get_value("Shift Type", args.shift_type):
		shift_type = frappe.get_doc(
			{
				"doctype": "Shift Type",
				"__newname": args.shift_type or "_Test Shift",
				"start_time": args.start_time or "08:00:00",
				"end_time": args.end_time or "12:00:00",
				"enable_auto_attendance": 1,
				"determine_check_in_and_check_out": "Alternating entries as IN and OUT during the same shift",
				"working_hours_calculation_based_on": "First Check-in and Last Check-out",
				"begin_check_in_before_shift_start_time": args.begin_check_in_before_shift_start_time or 60,
				"allow_check_out_after_shift_end_time": args.allow_check_out_after_shift_end_time or 60,
				"process_attendance_after": add_days(date, -2),
				"last_sync_of_checkin": args.last_sync_of_checkin or now_datetime() + timedelta(days=1),
				"mark_auto_attendance_on_holidays": args.mark_auto_attendance_on_holidays or 0,
				"allow_overtime": args.allow_overtime or 0,
				"overtime_type": args.overtime_type or None,
			}
		)
	else:
		shift_type = frappe.get_doc("Shift Type", args.shift_type)

	holiday_list = "Employee Checkin Test Holiday List"
	if not frappe.db.exists("Holiday List", "Employee Checkin Test Holiday List"):
		holiday_list = frappe.get_doc(
			{
				"doctype": "Holiday List",
				"holiday_list_name": "Employee Checkin Test Holiday List",
				"from_date": get_year_start(date),
				"to_date": get_year_ending(date),
			}
		).insert()
		holiday_list = holiday_list.name

	shift_type.holiday_list = holiday_list
	shift_type.update(args)
	shift_type.save()

	return shift_type


def make_shift_assignment(
	shift_type, employee, start_date, end_date=None, do_not_submit=False, shift_location=None
):
	shift_assignment = frappe.get_doc(
		{
			"doctype": "Shift Assignment",
			"shift_type": shift_type,
			"company": "_Test Company",
			"employee": employee,
			"start_date": start_date,
			"end_date": end_date,
			"shift_location": shift_location,
		}
	)
	if not do_not_submit:
		shift_assignment.submit()

	return shift_assignment
