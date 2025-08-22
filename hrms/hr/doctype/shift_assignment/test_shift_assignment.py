# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, get_datetime, getdate, nowdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.shift_assignment.shift_assignment import (
	MultipleShiftError,
	OverlappingShiftError,
	get_actual_start_end_datetime_of_shift,
	get_events,
)
from hrms.hr.doctype.shift_type.test_shift_type import make_shift_assignment, setup_shift_type
from hrms.tests.utils import HRMSTestSuite

test_dependencies = ["Shift Type"]


class TestShiftAssignment(HRMSTestSuite):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.make_employees()

	def setUp(self):
		frappe.db.delete("Shift Assignment")
		frappe.db.delete("Shift Type")

	def test_overlapping_for_ongoing_shift(self):
		shift = "Day Shift"
		employee = "_T-Employee-00001"
		date = nowdate()

		# shift should be Ongoing if Only start_date is present and status = Active
		setup_shift_type(shift_type=shift)
		make_shift_assignment(shift, employee, date)

		# shift ends before ongoing shift starts
		non_overlapping_shift = make_shift_assignment(shift, employee, add_days(date, -1), add_days(date, -1))
		self.assertEqual(non_overlapping_shift.docstatus, 1)

		overlapping_shift = make_shift_assignment(shift, employee, add_days(date, 2), do_not_submit=True)
		self.assertRaises(OverlappingShiftError, overlapping_shift.save)

	def test_multiple_shift_assignments_for_same_date(self):
		employee = "_T-Employee-00001"
		date = nowdate()

		setup_shift_type(shift_type="Day Shift")
		make_shift_assignment("Day Shift", employee, date)

		setup_shift_type(shift_type="Night Shift", start_time="19:00:00", end_time="23:00:00")
		assignment = make_shift_assignment("Night Shift", employee, date, do_not_submit=True)

		frappe.db.set_single_value("HR Settings", "allow_multiple_shift_assignments", 0)
		self.assertRaises(MultipleShiftError, assignment.save)
		frappe.db.set_single_value("HR Settings", "allow_multiple_shift_assignments", 1)
		assignment.save()  # would throw error if multiple shift assignments not allowed

	def test_overlapping_for_fixed_period_shift(self):
		shift = "Day Shift"
		employee = "_T-Employee-00001"
		date = nowdate()

		setup_shift_type(shift_type=shift)
		make_shift_assignment(shift, employee, date, add_days(date, 30))

		assignment = make_shift_assignment(
			shift, employee, add_days(date, 10), add_days(date, 35), do_not_submit=True
		)
		self.assertRaises(OverlappingShiftError, assignment.save)

	def test_overlapping_for_a_fixed_period_shift_and_ongoing_shift(self):
		employee = make_employee("test_shift_assignment@example.com", company="_Test Company")

		# shift setup for 8-12
		shift_type = setup_shift_type(shift_type="Shift 1", start_time="08:00:00", end_time="12:00:00")
		date = getdate()
		# shift with end date
		make_shift_assignment(shift_type.name, employee, date, add_days(date, 30))

		# shift setup for 11-15
		shift_type = setup_shift_type(shift_type="Shift 2", start_time="11:00:00", end_time="15:00:00")
		date = getdate()

		# shift assignment without end date
		assignment = make_shift_assignment("Shift 2", employee, date, do_not_submit=True)
		self.assertRaises(OverlappingShiftError, assignment.save)

	def test_overlap_for_shifts_on_same_day_with_overlapping_timeslots(self):
		employee = make_employee("test_shift_assignment@example.com", company="_Test Company")
		date = getdate()

		# shift setup for 8-12
		setup_shift_type(shift_type="Shift 1", start_time="08:00:00", end_time="12:00:00")
		make_shift_assignment("Shift 1", employee, date)

		# shift setup for 11-15
		setup_shift_type(shift_type="Shift 2", start_time="11:00:00", end_time="15:00:00")
		assignment = make_shift_assignment("Shift 2", employee, date, do_not_submit=True)
		self.assertRaises(OverlappingShiftError, assignment.save)

		# shift setup for 12-16
		setup_shift_type(shift_type="Shift 3", start_time="12:00:00", end_time="16:00:00")
		make_shift_assignment("Shift 3", employee, date)

		# shift setup for 15-19
		setup_shift_type(shift_type="Shift 4", start_time="15:00:00", end_time="19:00:00")
		assignment = make_shift_assignment("Shift 4", employee, date, do_not_submit=True)
		self.assertRaises(OverlappingShiftError, assignment.save)

	def test_overlap_for_midnight_shifts(self):
		employee = make_employee("test_shift_assignment@example.com", company="_Test Company")
		date = getdate()

		overlapping_shifts = [
			# s1(start, end), s2(start, end)
			[("22:00:00", "02:00:00"), ("21:00:00", "23:00:00")],
			[("22:00:00", "02:00:00"), ("20:00:00", "01:00:00")],
			[("01:00:00", "02:00:00"), ("01:30:00", "03:00:00")],
			[("21:00:00", "23:00:00"), ("22:00:00", "03:00:00")],
		]

		for i, pair in enumerate(overlapping_shifts):
			s1 = setup_shift_type(shift_type=f"Shift 1-{i}", start_time=pair[0][0], end_time=pair[0][1])
			s2 = setup_shift_type(shift_type=f"Shift 2-{i}", start_time=pair[1][0], end_time=pair[1][1])

			assignment1 = make_shift_assignment(s1.name, employee, date)
			assignment = make_shift_assignment(s2.name, employee, date, do_not_submit=True)

			self.assertRaises(OverlappingShiftError, assignment.insert)

			assignment1.cancel()

		shift_type = setup_shift_type(shift_type="Shift 1", start_time="20:00:00", end_time="01:00:00")
		make_shift_assignment(shift_type.name, employee, date)

		# no overlap
		shift_type = setup_shift_type(shift_type="Shift 2", start_time="15:00:00", end_time="20:00:00")
		assignment = make_shift_assignment(shift_type.name, employee, date)

		# no overlap
		shift_type = setup_shift_type(shift_type="Shift 3", start_time="01:00:00", end_time="05:00:00")
		assignment = make_shift_assignment(shift_type.name, employee, date)

		# overlap
		shift_type = setup_shift_type(shift_type="Shift 4", start_time="21:00:00", end_time="02:00:00")
		assignment = make_shift_assignment(shift_type.name, employee, date, do_not_submit=True)
		self.assertRaises(OverlappingShiftError, assignment.save)

	def test_calendar(self):
		employee1 = make_employee("test_shift_assignment1@example.com", company="_Test Company")
		employee2 = make_employee("test_shift_assignment2@example.com", company="_Test Company")
		employee3 = make_employee("test_shift_assignment3@example.com", company="_Test Company")

		shift_type = setup_shift_type(shift_type="Shift 1", start_time="08:00:00", end_time="12:00:00")
		date = getdate()
		shift1 = make_shift_assignment(shift_type.name, employee1, date)  # 1 day
		make_shift_assignment(shift_type.name, employee2, date)  # excluded due to employee filter
		make_shift_assignment(shift_type.name, employee3, add_days(date, -3), add_days(date, -2))  # excluded
		shift2 = make_shift_assignment(shift_type.name, employee3, add_days(date, -1), date)  # 2 days
		shift3 = make_shift_assignment(
			shift_type.name, employee3, add_days(date, 1), add_days(date, 2)
		)  # 2 days
		shift4 = make_shift_assignment(
			shift_type.name, employee3, add_days(date, 30), add_days(date, 30)
		)  # 1 day
		make_shift_assignment(shift_type.name, employee3, add_days(date, 31))  # excluded

		events = get_events(
			start=date,
			end=add_days(date, 30),
			filters=[["Shift Assignment", "employee", "!=", employee2, False]],
		)
		self.assertEqual(len(events), 6)
		for shift in events:
			self.assertIn(shift["name"], [shift1.name, shift2.name, shift3.name, shift4.name])

	def test_calendar_for_night_shift(self):
		employee1 = make_employee("test_shift_assignment1@example.com", company="_Test Company")

		shift_type = setup_shift_type(shift_type="Shift 1", start_time="08:00:00", end_time="02:00:00")
		date = getdate()
		make_shift_assignment(shift_type.name, employee1, date, date)

		events = get_events(start=date, end=date)
		self.assertEqual(events[0]["start_date"], get_datetime(f"{date} 08:00:00"))
		self.assertEqual(events[0]["end_date"], get_datetime(f"{add_days(date, 1)} 02:00:00"))

	def test_consecutive_day_and_night_shifts(self):
		# defaults
		employee = make_employee("test_default_shift_assignment@example.com", company="_Test Company")
		today = getdate()
		yesterday = add_days(today, -1)

		# default shift
		shift_type = setup_shift_type(shift_type="Test Security", start_time="07:00:00", end_time="19:00:00")
		frappe.db.set_value("Employee", employee, "default_shift", shift_type.name)

		# night shift
		shift_type = setup_shift_type(
			shift_type="Test Security - Night", start_time="19:00:00", end_time="07:00:00"
		)
		make_shift_assignment(shift_type.name, employee, yesterday, yesterday)

		# prev shift log
		prev_shift = get_actual_start_end_datetime_of_shift(employee, get_datetime(f"{today} 07:00:00"), True)
		self.assertEqual(prev_shift.shift_type.name, "Test Security - Night")
		self.assertEqual(prev_shift.actual_start.date(), yesterday)
		self.assertEqual(prev_shift.actual_end.date(), today)

		# current shift IN
		checkin = get_actual_start_end_datetime_of_shift(employee, get_datetime(f"{today} 07:01:00"), True)
		# current shift OUT
		checkout = get_actual_start_end_datetime_of_shift(employee, get_datetime(f"{today} 19:00:00"), True)
		self.assertEqual(checkin.shift_type, checkout.shift_type)
		self.assertEqual(checkin.actual_start.date(), today)
		self.assertEqual(checkout.actual_end.date(), today)

	def test_shift_details_on_consecutive_days_with_overlapping_timings(self):
		# defaults
		employee = make_employee("test_shift_assignment@example.com", company="_Test Company")
		today = getdate()
		yesterday = add_days(today, -1)

		# shift 1
		shift_type = setup_shift_type(shift_type="Morning", start_time="07:00:00", end_time="12:00:00")
		make_shift_assignment(shift_type.name, employee, add_days(yesterday, -1), yesterday)

		# shift 2
		shift_type = setup_shift_type(shift_type="Afternoon", start_time="09:30:00", end_time="14:00:00")
		make_shift_assignment(shift_type.name, employee, today, add_days(today, 1))

		# current_shift shift log - checkin in the grace period of current shift, non-overlapping with prev shift
		current_shift = get_actual_start_end_datetime_of_shift(
			employee, get_datetime(f"{today} 14:01:00"), True
		)
		self.assertEqual(current_shift.shift_type.name, "Afternoon")
		self.assertEqual(current_shift.actual_start, get_datetime(f"{today} 08:30:00"))
		self.assertEqual(current_shift.actual_end, get_datetime(f"{today} 15:00:00"))

		# previous shift
		checkin = get_actual_start_end_datetime_of_shift(
			employee, get_datetime(f"{yesterday} 07:01:00"), True
		)
		checkout = get_actual_start_end_datetime_of_shift(
			employee, get_datetime(f"{yesterday} 13:00:00"), True
		)
		self.assertTrue(checkin.shift_type.name == checkout.shift_type.name == "Morning")
		self.assertEqual(checkin.actual_start, get_datetime(f"{yesterday} 06:00:00"))
		self.assertEqual(checkout.actual_end, get_datetime(f"{yesterday} 13:00:00"))
