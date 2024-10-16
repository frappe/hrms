# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from datetime import datetime, timedelta

import frappe
from frappe.tests import IntegrationTestCase, change_settings
from frappe.utils import (
	add_days,
	get_time,
	get_year_ending,
	get_year_start,
	getdate,
	now_datetime,
	nowdate,
)

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.employee_checkin.employee_checkin import (
	CheckinRadiusExceededError,
	add_log_based_on_employee_field,
	bulk_fetch_shift,
	calculate_working_hours,
	mark_attendance_and_link_log,
)
from hrms.hr.doctype.shift_type.test_shift_type import make_shift_assignment, setup_shift_type
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_holiday_list


class TestEmployeeCheckin(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("Shift Type")
		frappe.db.delete("Shift Assignment")
		frappe.db.delete("Employee Checkin")

		from_date = get_year_start(getdate())
		to_date = get_year_ending(getdate())
		self.holiday_list = make_holiday_list(from_date=from_date, to_date=to_date)

		frappe.db.set_single_value("HR Settings", "allow_geolocation_tracking", 0)

	def test_geolocation_tracking(self):
		employee = make_employee("test_add_log_based_on_employee_field@example.com")
		checkin = make_checkin(employee)
		checkin.latitude = 23.31773
		checkin.longitude = 66.82876
		checkin.save()

		# geolocation tracking is disabled
		self.assertIsNone(checkin.geolocation)

		frappe.db.set_single_value("HR Settings", "allow_geolocation_tracking", 1)

		checkin.save()
		self.assertEqual(
			checkin.geolocation,
			frappe.json.dumps(
				{
					"type": "FeatureCollection",
					"features": [
						{
							"type": "Feature",
							"properties": {},
							"geometry": {"type": "Point", "coordinates": [66.82876, 23.31773]},
						}
					],
				}
			),
		)

	def test_add_log_based_on_employee_field(self):
		employee = make_employee("test_add_log_based_on_employee_field@example.com")
		employee = frappe.get_doc("Employee", employee)
		employee.attendance_device_id = "3344"
		employee.save()

		time_now = now_datetime().__str__()[:-7]
		employee_checkin = add_log_based_on_employee_field("3344", time_now, "mumbai_first_floor", "IN")
		self.assertEqual(employee_checkin.employee, employee.name)
		self.assertEqual(employee_checkin.time, time_now)
		self.assertEqual(employee_checkin.device_id, "mumbai_first_floor")
		self.assertEqual(employee_checkin.log_type, "IN")

	def test_mark_attendance_and_link_log(self):
		employee = make_employee("test_mark_attendance_and_link_log@example.com")
		logs = make_n_checkins(employee, 3)
		mark_attendance_and_link_log(logs, "Skip", nowdate())
		log_names = [log.name for log in logs]
		logs_count = frappe.db.count(
			"Employee Checkin", {"name": ["in", log_names], "skip_auto_attendance": 1}
		)
		self.assertEqual(logs_count, 3)

		logs = make_n_checkins(employee, 4, 2)
		now_date = nowdate()
		frappe.db.delete("Attendance", {"employee": employee})
		attendance = mark_attendance_and_link_log(logs, "Present", now_date, 8.2)
		log_names = [log.name for log in logs]
		logs_count = frappe.db.count(
			"Employee Checkin", {"name": ["in", log_names], "attendance": attendance.name}
		)
		self.assertEqual(logs_count, 4)
		attendance_count = frappe.db.count(
			"Attendance",
			{"status": "Present", "working_hours": 8.2, "employee": employee, "attendance_date": now_date},
		)
		self.assertEqual(attendance_count, 1)

	def test_unlink_attendance_on_cancellation(self):
		employee = make_employee("test_mark_attendance_and_link_log@example.com")
		logs = make_n_checkins(employee, 3)

		frappe.db.delete("Attendance", {"employee": employee})
		attendance = mark_attendance_and_link_log(logs, "Present", nowdate(), 8.2)
		attendance.cancel()

		linked_logs = frappe.db.get_all("Employee Checkin", {"attendance": attendance.name})
		self.assertEqual(len(linked_logs), 0)

	def test_calculate_working_hours(self):
		check_in_out_type = [
			"Alternating entries as IN and OUT during the same shift",
			"Strictly based on Log Type in Employee Checkin",
		]
		working_hours_calc_type = [
			"First Check-in and Last Check-out",
			"Every Valid Check-in and Check-out",
		]
		logs_type_1 = [
			{"time": now_datetime() - timedelta(minutes=390)},
			{"time": now_datetime() - timedelta(minutes=300)},
			{"time": now_datetime() - timedelta(minutes=270)},
			{"time": now_datetime() - timedelta(minutes=90)},
			{"time": now_datetime() - timedelta(minutes=0)},
		]
		logs_type_2 = [
			{"time": now_datetime() - timedelta(minutes=390), "log_type": "OUT"},
			{"time": now_datetime() - timedelta(minutes=360), "log_type": "IN"},
			{"time": now_datetime() - timedelta(minutes=300), "log_type": "OUT"},
			{"time": now_datetime() - timedelta(minutes=290), "log_type": "IN"},
			{"time": now_datetime() - timedelta(minutes=260), "log_type": "OUT"},
			{"time": now_datetime() - timedelta(minutes=240), "log_type": "IN"},
			{"time": now_datetime() - timedelta(minutes=150), "log_type": "IN"},
			{"time": now_datetime() - timedelta(minutes=60), "log_type": "OUT"},
		]
		logs_type_1 = [frappe._dict(x) for x in logs_type_1]
		logs_type_2 = [frappe._dict(x) for x in logs_type_2]

		working_hours = calculate_working_hours(logs_type_1, check_in_out_type[0], working_hours_calc_type[0])
		self.assertEqual(working_hours, (6.5, logs_type_1[0].time, logs_type_1[-1].time))

		working_hours = calculate_working_hours(logs_type_1, check_in_out_type[0], working_hours_calc_type[1])
		self.assertEqual(working_hours, (4.5, logs_type_1[0].time, logs_type_1[-1].time))

		working_hours = calculate_working_hours(logs_type_2, check_in_out_type[1], working_hours_calc_type[0])
		self.assertEqual(working_hours, (5, logs_type_2[1].time, logs_type_2[-1].time))

		working_hours = calculate_working_hours(logs_type_2, check_in_out_type[1], working_hours_calc_type[1])
		self.assertEqual(working_hours, (4.5, logs_type_2[1].time, logs_type_2[-1].time))

		working_hours = calculate_working_hours(
			[logs_type_2[1], logs_type_2[-1]], check_in_out_type[1], working_hours_calc_type[1]
		)
		self.assertEqual(working_hours, (5.0, logs_type_2[1].time, logs_type_2[-1].time))

	def test_fetch_shift(self):
		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")

		# shift setup for 8-12
		shift_type = setup_shift_type()
		date = getdate()
		make_shift_assignment(shift_type.name, employee, date)

		# within shift time
		timestamp = datetime.combine(date, get_time("08:45:00"))
		log = make_checkin(employee, timestamp)
		self.assertEqual(log.shift, shift_type.name)

		# "begin checkin before shift time" = 60 mins, so should work for 7:00:00
		timestamp = datetime.combine(date, get_time("07:00:00"))
		log = make_checkin(employee, timestamp)
		self.assertEqual(log.shift, shift_type.name)

		# "allow checkout after shift end time" = 60 mins, so should work for 13:00:00
		timestamp = datetime.combine(date, get_time("13:00:00"))
		log = make_checkin(employee, timestamp)
		self.assertEqual(log.shift, shift_type.name)

		# should not fetch this shift beyond allowed time
		timestamp = datetime.combine(date, get_time("13:01:00"))
		log = make_checkin(employee, timestamp)
		self.assertIsNone(log.shift)

	@change_settings("HR Settings", {"allow_multiple_shift_assignments": 1})
	def test_fetch_shift_for_assignment_with_end_date(self):
		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")

		# shift setup for 8-12
		shift1 = setup_shift_type()
		# 12:30 - 16:30
		shift2 = setup_shift_type(shift_type="Shift 2", start_time="12:30:00", end_time="16:30:00")

		date = getdate()
		make_shift_assignment(shift1.name, employee, date, add_days(date, 15))
		make_shift_assignment(shift2.name, employee, date, add_days(date, 15))

		timestamp = datetime.combine(date, get_time("08:45:00"))
		log = make_checkin(employee, timestamp)
		self.assertEqual(log.shift, shift1.name)

		timestamp = datetime.combine(date, get_time("12:45:00"))
		log = make_checkin(employee, timestamp)
		self.assertEqual(log.shift, shift2.name)

		# log after end date
		timestamp = datetime.combine(add_days(date, 16), get_time("12:45:00"))
		log = make_checkin(employee, timestamp)
		self.assertIsNone(log.shift)

	def test_shift_start_and_end_timings(self):
		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")

		# shift setup for 8-12
		shift_type = setup_shift_type()
		date = getdate()
		make_shift_assignment(shift_type.name, employee, date)

		timestamp = datetime.combine(date, get_time("08:45:00"))
		log = make_checkin(employee, timestamp)

		self.assertEqual(log.shift, shift_type.name)
		self.assertEqual(log.shift_start, datetime.combine(date, get_time("08:00:00")))
		self.assertEqual(log.shift_end, datetime.combine(date, get_time("12:00:00")))
		self.assertEqual(log.shift_actual_start, datetime.combine(date, get_time("07:00:00")))
		self.assertEqual(log.shift_actual_end, datetime.combine(date, get_time("13:00:00")))

	def test_fetch_shift_based_on_default_shift(self):
		employee = make_employee("test_default_shift@example.com", company="_Test Company")
		default_shift = setup_shift_type(
			shift_type="Default Shift", start_time="14:00:00", end_time="16:00:00"
		)

		date = getdate()
		frappe.db.set_value("Employee", employee, "default_shift", default_shift.name)

		timestamp = datetime.combine(date, get_time("14:45:00"))
		log = make_checkin(employee, timestamp)

		# should consider default shift
		self.assertEqual(log.shift, default_shift.name)

	def test_fetch_night_shift_for_assignment_without_end_date(self):
		"""Tests if shift is correctly fetched in logs when assignment has no end date"""
		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")
		shift_type = setup_shift_type(shift_type="Midnight Shift", start_time="23:00:00", end_time="01:00:00")
		date = getdate()
		next_day = add_days(date, 1)
		make_shift_assignment(shift_type.name, employee, date)

		# log falls in the first day
		timestamp = datetime.combine(date, get_time("23:00:00"))
		log_in = make_checkin(employee, timestamp)

		# log falls in the second day
		timestamp = datetime.combine(next_day, get_time("01:30:00"))
		log_out = make_checkin(employee, timestamp)

		for log in [log_in, log_out]:
			self.assertEqual(log.shift, shift_type.name)
			self.assertEqual(log.shift_start, datetime.combine(date, get_time("23:00:00")))
			self.assertEqual(log.shift_end, datetime.combine(next_day, get_time("01:00:00")))
			self.assertEqual(log.shift_actual_start, datetime.combine(date, get_time("22:00:00")))
			self.assertEqual(log.shift_actual_end, datetime.combine(next_day, get_time("02:00:00")))

	def test_fetch_night_shift_on_assignment_boundary(self):
		"""
		Tests if shift is correctly fetched in logs when assignment starts and ends on the same day
		"""
		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")
		shift_type = setup_shift_type(shift_type="Midnight Shift", start_time="23:00:00", end_time="07:00:00")
		date = getdate()
		next_day = add_days(date, 1)

		# shift assigned for a single day
		make_shift_assignment(shift_type.name, employee, date, date)

		# IN log falls on the first day
		start_timestamp = datetime.combine(date, get_time("23:00:00"))
		log_in = make_checkin(employee, start_timestamp)

		# OUT log falls on the second day
		end_timestamp = datetime.combine(next_day, get_time("7:00:00"))
		log_out = make_checkin(employee, end_timestamp)

		for log in [log_in, log_out]:
			self.assertEqual(log.shift, shift_type.name)
			self.assertEqual(log.shift_start, start_timestamp)
			self.assertEqual(log.shift_end, end_timestamp)

	def test_night_shift_not_fetched_outside_assignment_boundary_for_diff_start_date(self):
		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")
		shift_type = setup_shift_type(shift_type="Midnight Shift", start_time="23:00:00", end_time="07:00:00")
		date = getdate()
		next_day = add_days(date, 1)
		prev_day = add_days(date, -1)

		# shift assigned for a single day
		make_shift_assignment(shift_type.name, employee, date, date)

		# shift not applicable on next day's start time
		log = make_checkin(employee, datetime.combine(next_day, get_time("23:00:00")))
		self.assertIsNone(log.shift)

		# shift not applicable on current day's end time
		log = make_checkin(employee, datetime.combine(date, get_time("07:00:00")))
		self.assertIsNone(log.shift)

		# shift not applicable on prev day's start time
		log = make_checkin(employee, datetime.combine(prev_day, get_time("23:00:00")))
		self.assertIsNone(log.shift)

	def test_night_shift_not_fetched_outside_assignment_boundary_for_diff_end_date(self):
		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")
		shift_type = setup_shift_type(shift_type="Midnight Shift", start_time="19:00:00", end_time="00:30:00")
		date = getdate()
		next_day = add_days(date, 1)
		prev_day = add_days(date, -1)

		# shift assigned for a single day
		make_shift_assignment(shift_type.name, employee, date, date)

		# shift not applicable on next day's start time
		log = make_checkin(employee, datetime.combine(next_day, get_time("19:00:00")))
		self.assertIsNone(log.shift)

		# shift not applicable on current day's end time
		log = make_checkin(employee, datetime.combine(date, get_time("00:30:00")))
		self.assertIsNone(log.shift)

		# shift not applicable on prev day's start time
		log = make_checkin(employee, datetime.combine(prev_day, get_time("19:00:00")))
		self.assertIsNone(log.shift)

	def test_night_shift_not_fetched_outside_before_shift_margin(self):
		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")
		shift_type = setup_shift_type(shift_type="Midnight Shift", start_time="00:30:00", end_time="10:00:00")
		date = getdate()
		next_day = add_days(date, 1)
		prev_day = add_days(date, -1)

		# shift assigned for a single day
		make_shift_assignment(shift_type.name, employee, date, date)

		# shift not fetched in today's shift margin
		log = make_checkin(employee, datetime.combine(date, get_time("23:30:00")))
		self.assertIsNone(log.shift)

		# shift not applicable on next day's start time
		log = make_checkin(employee, datetime.combine(next_day, get_time("00:30:00")))
		self.assertIsNone(log.shift)

		# shift not applicable on prev day's start time
		log = make_checkin(employee, datetime.combine(prev_day, get_time("00:30:00")))
		self.assertIsNone(log.shift)

	def test_night_shift_not_fetched_outside_after_shift_margin(self):
		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")
		shift_type = setup_shift_type(shift_type="Midnight Shift", start_time="15:00:00", end_time="23:30:00")
		date = getdate()
		next_day = add_days(date, 1)
		prev_day = add_days(date, -1)

		# shift assigned for a single day
		make_shift_assignment(shift_type.name, employee, date, date)

		# shift not fetched in today's shift margin
		log = make_checkin(employee, datetime.combine(date, get_time("00:30:00")))
		self.assertIsNone(log.shift)

		# shift not applicable on next day's start time
		log = make_checkin(employee, datetime.combine(next_day, get_time("15:00:00")))
		self.assertIsNone(log.shift)

		# shift not applicable on prev day's start time
		log = make_checkin(employee, datetime.combine(prev_day, get_time("15:00:00")))
		self.assertIsNone(log.shift)

		# shift not applicable on prev day's end time
		log = make_checkin(employee, datetime.combine(prev_day, get_time("00:30:00")))
		self.assertIsNone(log.shift)

	def test_fetch_night_shift_in_margin_period_after_shift(self):
		"""
		Tests if shift is correctly fetched in logs if the actual end time exceeds a day
		i.e: shift is from 15:00 to 23:00 (starts & ends on the same day)
		but shift margin = 2 hours, so the actual shift goes to 1:00 of the next day
		"""
		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")
		# shift margin goes to next day (1:00 am)
		shift_type = setup_shift_type(
			shift_type="Midnight Shift",
			start_time="15:00:00",
			end_time="23:00:00",
			allow_check_out_after_shift_end_time=120,
		)
		date = getdate()
		next_day = add_days(date, 1)

		# shift assigned for a single day
		make_shift_assignment(shift_type.name, employee, date, date)

		# IN log falls on the first day
		start_timestamp = datetime.combine(date, get_time("14:00:00"))
		log_in = make_checkin(employee, start_timestamp)

		# OUT log falls on the second day in the shift margin period
		end_timestamp = datetime.combine(next_day, get_time("01:00:00"))
		log_out = make_checkin(employee, end_timestamp)

		for log in [log_in, log_out]:
			self.assertEqual(log.shift, shift_type.name)
			self.assertEqual(log.shift_actual_start, start_timestamp)
			self.assertEqual(log.shift_actual_end, end_timestamp)

	def test_fetch_night_shift_in_margin_period_before_shift(self):
		"""
		Tests if shift is correctly fetched in logs if the actual end time exceeds a day
		i.e: shift is from 00:30 to 10:00 (starts & ends on the same day)
		but shift margin = 1 hour, so the actual shift start goes to 23:30:00 of the prev day
		"""
		employee = make_employee("test_employee_checkin@example.com", company="_Test Company")
		# shift margin goes to next day (1:00 am)
		shift_type = setup_shift_type(
			shift_type="Midnight Shift",
			start_time="00:30:00",
			end_time="10:00:00",
		)
		date = getdate()
		prev_day = add_days(date, -1)

		# shift assigned for a single day
		make_shift_assignment(shift_type.name, employee, date, date)

		# IN log falls on the first day in the shift margin period
		start_timestamp = datetime.combine(prev_day, get_time("23:30:00"))
		log_in = make_checkin(employee, start_timestamp)

		# OUT log falls on the second day
		end_timestamp = datetime.combine(date, get_time("11:00:00"))
		log_out = make_checkin(employee, end_timestamp)

		for log in [log_in, log_out]:
			self.assertEqual(log.shift, shift_type.name)
			self.assertEqual(log.shift_actual_start, start_timestamp)
			self.assertEqual(log.shift_actual_end, end_timestamp)

	@change_settings("HR Settings", {"allow_multiple_shift_assignments": 1})
	def test_consecutive_shift_assignments_overlapping_within_grace_period(self):
		# test adjustment for start and end times if they are overlapping
		# within "begin_check_in_before_shift_start_time" and "allow_check_out_after_shift_end_time" periods
		employee = make_employee("test_shift@example.com", company="_Test Company")

		# 8 - 12
		shift1 = setup_shift_type()
		# 12:30 - 16:30
		shift2 = setup_shift_type(shift_type="Consecutive Shift", start_time="12:30:00", end_time="16:30:00")

		# the actual start and end times (with grace) for these shifts are 7 - 13 and 11:30 - 17:30
		date = getdate()
		make_shift_assignment(shift1.name, employee, date)
		make_shift_assignment(shift2.name, employee, date)

		# log at 12:30 should set shift2 and actual start as 12 and not 11:30
		timestamp = datetime.combine(date, get_time("12:30:00"))
		log = make_checkin(employee, timestamp)
		self.assertEqual(log.shift, shift2.name)
		self.assertEqual(log.shift_start, datetime.combine(date, get_time("12:30:00")))
		self.assertEqual(log.shift_actual_start, datetime.combine(date, get_time("12:00:00")))

		# log at 12:00 should set shift1 and actual end as 12 and not 1 since the next shift's grace starts
		timestamp = datetime.combine(date, get_time("12:00:00"))
		log = make_checkin(employee, timestamp)
		self.assertEqual(log.shift, shift1.name)
		self.assertEqual(log.shift_end, datetime.combine(date, get_time("12:00:00")))
		self.assertEqual(log.shift_actual_end, datetime.combine(date, get_time("12:00:00")))

		# log at 12:01 should set shift2
		timestamp = datetime.combine(date, get_time("12:01:00"))
		log = make_checkin(employee, timestamp)
		self.assertEqual(log.shift, shift2.name)

	@change_settings("HR Settings", {"allow_multiple_shift_assignments": 1})
	@change_settings("HR Settings", {"allow_geolocation_tracking": 1})
	def test_geofencing(self):
		employee = make_employee("test_shift@example.com", company="_Test Company")

		# 8 - 12
		shift1 = setup_shift_type()
		# 15 - 19
		shift2 = setup_shift_type(shift_type="Consecutive Shift", start_time="15:00:00", end_time="19:00:00")

		date = getdate()
		location1 = make_shift_location("Loc A", 24, 72)
		location2 = make_shift_location("Loc B", 25, 75, checkin_radius=2000)
		make_shift_assignment(shift1.name, employee, date, shift_location=location1.name)
		make_shift_assignment(shift2.name, employee, date, shift_location=location2.name)

		timestamp = datetime.combine(add_days(date, -1), get_time("11:00:00"))
		# allowed as it is before the shift start date
		make_checkin(employee, timestamp, 20, 65)

		timestamp = datetime.combine(date, get_time("06:00:00"))
		# allowed as it is before the shift start time
		make_checkin(employee, timestamp, 20, 65)

		timestamp = datetime.combine(date, get_time("10:00:00"))
		# allowed as distance (150m) is within checkin radius (500m)
		make_checkin(employee, timestamp, 24.001, 72.001)

		timestamp = datetime.combine(date, get_time("10:30:00"))
		log = frappe.get_doc(
			{
				"doctype": "Employee Checkin",
				"employee": employee,
				"time": timestamp,
				"latitude": 24.01,
				"longitude": 72.01,
			}
		)
		# not allowed as distance (1506m) is not within checkin radius
		self.assertRaises(CheckinRadiusExceededError, log.insert)

		# to ensure that the correct shift assignment is considered
		timestamp = datetime.combine(date, get_time("16:00:00"))
		# allowed as distance (1506m) is within checkin radius (2000m)
		make_checkin(employee, timestamp, 25.01, 75.01)

		timestamp = datetime.combine(date, get_time("16:30:00"))
		log = frappe.get_doc(
			{
				"doctype": "Employee Checkin",
				"employee": employee,
				"time": timestamp,
				"latitude": 25.1,
				"longitude": 75.1,
			}
		)
		# not allowed as distance (15004m) is not within checkin radius
		self.assertRaises(CheckinRadiusExceededError, log.insert)


def make_n_checkins(employee, n, hours_to_reverse=1):
	logs = [make_checkin(employee, now_datetime() - timedelta(hours=hours_to_reverse, minutes=n + 1))]
	for i in range(n - 1):
		logs.append(make_checkin(employee, now_datetime() - timedelta(hours=hours_to_reverse, minutes=n - i)))
	return logs


def make_checkin(employee, time=None, latitude=None, longitude=None):
	if not time:
		time = now_datetime()

	log = frappe.get_doc(
		{
			"doctype": "Employee Checkin",
			"employee": employee,
			"time": time,
			"device_id": "device1",
			"log_type": "IN",
			"latitude": latitude,
			"longitude": longitude,
		}
	).insert()
	return log


def make_shift_location(location_name, latitude, longitude, checkin_radius=500):
	shift_location = frappe.get_doc(
		{
			"doctype": "Shift Location",
			"location_name": location_name,
			"latitude": latitude,
			"longitude": longitude,
			"checkin_radius": checkin_radius,
		}
	).insert()

	return shift_location
