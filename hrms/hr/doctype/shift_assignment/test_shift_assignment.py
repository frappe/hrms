# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import unittest

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, get_datetime, getdate, nowdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.shift_assignment.shift_assignment import (
	OverlappingShiftError,
	get_actual_start_end_datetime_of_shift,
	get_events,
)
from hrms.hr.doctype.shift_type.test_shift_type import make_shift_assignment, setup_shift_type

test_dependencies = ["Shift Type"]


class TestShiftAssignment(FrappeTestCase):
	def setUp(self):
		frappe.db.delete("Shift Assignment")
		frappe.db.delete("Shift Type")

	def test_make_shift_assignment(self):
		setup_shift_type(shift_type="Day Shift")
		shift_assignment = frappe.get_doc(
			{
				"doctype": "Shift Assignment",
				"shift_type": "Day Shift",
				"company": "_Test Company",
				"employee": "_T-Employee-00001",
				"start_date": nowdate(),
			}
		).insert()
		shift_assignment.submit()

		self.assertEqual(shift_assignment.docstatus, 1)

	def test_overlapping_for_ongoing_shift(self):
		# shift should be Ongoing if Only start_date is present and status = Active
		setup_shift_type(shift_type="Day Shift")
		shift_assignment_1 = frappe.get_doc(
			{
				"doctype": "Shift Assignment",
				"shift_type": "Day Shift",
				"company": "_Test Company",
				"employee": "_T-Employee-00001",
				"start_date": nowdate(),
				"status": "Active",
			}
		).insert()
		shift_assignment_1.submit()

		self.assertEqual(shift_assignment_1.docstatus, 1)

		shift_assignment = frappe.get_doc(
			{
				"doctype": "Shift Assignment",
				"shift_type": "Day Shift",
				"company": "_Test Company",
				"employee": "_T-Employee-00001",
				"start_date": add_days(nowdate(), 2),
			}
		)

		self.assertRaises(OverlappingShiftError, shift_assignment.save)

	def test_overlapping_for_fixed_period_shift(self):
		# shift should is for Fixed period if Only start_date and end_date both are present and status = Active
		setup_shift_type(shift_type="Day Shift")
		shift_assignment_1 = frappe.get_doc(
			{
				"doctype": "Shift Assignment",
				"shift_type": "Day Shift",
				"company": "_Test Company",
				"employee": "_T-Employee-00001",
				"start_date": nowdate(),
				"end_date": add_days(nowdate(), 30),
				"status": "Active",
			}
		).insert()
		shift_assignment_1.submit()

		# it should not allowed within period of any shift.
		shift_assignment_3 = frappe.get_doc(
			{
				"doctype": "Shift Assignment",
				"shift_type": "Day Shift",
				"company": "_Test Company",
				"employee": "_T-Employee-00001",
				"start_date": add_days(nowdate(), 10),
				"end_date": add_days(nowdate(), 35),
				"status": "Active",
			}
		)

		self.assertRaises(OverlappingShiftError, shift_assignment_3.save)

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
		shift2 = frappe.get_doc(
			{
				"doctype": "Shift Assignment",
				"shift_type": shift_type.name,
				"company": "_Test Company",
				"employee": employee,
				"start_date": date,
			}
		)
		self.assertRaises(OverlappingShiftError, shift2.insert)

	def test_overlap_for_shifts_on_same_day_with_overlapping_timeslots(self):
		employee = make_employee("test_shift_assignment@example.com", company="_Test Company")

		# shift setup for 8-12
		shift_type = setup_shift_type(shift_type="Shift 1", start_time="08:00:00", end_time="12:00:00")
		date = getdate()
		make_shift_assignment(shift_type.name, employee, date)

		# shift setup for 11-15
		shift_type = setup_shift_type(shift_type="Shift 2", start_time="11:00:00", end_time="15:00:00")
		shift2 = frappe.get_doc(
			{
				"doctype": "Shift Assignment",
				"shift_type": shift_type.name,
				"company": "_Test Company",
				"employee": employee,
				"start_date": date,
			}
		)
		self.assertRaises(OverlappingShiftError, shift2.insert)

	def test_overlap_for_midnight_shifts(self):
		employee = make_employee("test_shift_assignment@example.com", company="_Test Company")
		date = getdate()

		overlapping_shifts = [
			# s1(start, end), s2(start, end)
			[("22:00:00", "02:00:00"), ("21:00:00", "23:00:00")],
			[("22:00:00", "02:00:00"), ("01:00:00", "03:00:00")],
			[("22:00:00", "02:00:00"), ("20:00:00", "01:00:00")],
			[("01:00:00", "02:00:00"), ("01:30:00", "03:00:00")],
			[("01:00:00", "02:00:00"), ("22:00:00", "03:00:00")],
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
		shift_type.update({"start_time": "02:00:00", "end_time": "3:00:00"})
		shift_type.save()
		assignment = make_shift_assignment(shift_type.name, employee, date)

	def test_multiple_shift_assignments_for_same_day(self):
		employee = make_employee("test_shift_assignment@example.com", company="_Test Company")

		# shift setup for 8-12
		shift_type = setup_shift_type(shift_type="Shift 1", start_time="08:00:00", end_time="12:00:00")
		date = getdate()
		make_shift_assignment(shift_type.name, employee, date)

		# shift setup for 13-15
		shift_type = setup_shift_type(shift_type="Shift 2", start_time="13:00:00", end_time="15:00:00")
		date = getdate()
		make_shift_assignment(shift_type.name, employee, date)

	def test_shift_assignment_calendar(self):
		employee1 = make_employee("test_shift_assignment1@example.com", company="_Test Company")
		employee2 = make_employee("test_shift_assignment2@example.com", company="_Test Company")

		shift_type = setup_shift_type(shift_type="Shift 1", start_time="08:00:00", end_time="12:00:00")
		date = getdate()
		shift1 = make_shift_assignment(shift_type.name, employee1, date)
		make_shift_assignment(shift_type.name, employee2, date)

		events = get_events(
			start=date, end=date, filters=[["Shift Assignment", "employee", "=", employee1, False]]
		)
		self.assertEqual(len(events), 1)
		self.assertEqual(events[0]["name"], shift1.name)

	def test_consecutive_day_and_night_shifts(self):
		# defaults
		employee = make_employee("test_shift_assignment@example.com", company="_Test Company")
		today = getdate()
		yesterday = add_days(today, -1)

		# default shift
		shift_type = setup_shift_type(
			shift_type="Test Security", start_time="07:00:00", end_time="19:00:00"
		)
		frappe.db.set_value("Employee", employee, "default_shift", shift_type.name)

		# night shift
		shift_type = setup_shift_type(
			shift_type="Test Security - Night", start_time="19:00:00", end_time="07:00:00"
		)
		make_shift_assignment(shift_type.name, employee, yesterday, yesterday)

		# prev shift log
		prev_shift = get_actual_start_end_datetime_of_shift(
			employee, get_datetime(f"{today} 07:00:00"), True
		)
		self.assertEqual(prev_shift.shift_type.name, "Test Security - Night")
		self.assertEqual(prev_shift.actual_start.date(), yesterday)
		self.assertEqual(prev_shift.actual_end.date(), today)

		# current shift IN
		checkin = get_actual_start_end_datetime_of_shift(
			employee, get_datetime(f"{today} 07:01:00"), True
		)
		# current shift OUT
		checkout = get_actual_start_end_datetime_of_shift(
			employee, get_datetime(f"{today} 19:00:00"), True
		)
		self.assertEqual(checkin.shift_type, checkout.shift_type)
		self.assertEqual(checkin.actual_start.date(), today)
		self.assertEqual(checkout.actual_end.date(), today)
