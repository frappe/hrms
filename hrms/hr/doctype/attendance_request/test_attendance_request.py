# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import unittest

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, add_months, get_year_ending, get_year_start, getdate

from hrms.hr.doctype.attendance.attendance import mark_attendance
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_holiday_list
from hrms.tests.test_utils import get_first_sunday

test_dependencies = ["Employee"]


class TestAttendanceRequest(FrappeTestCase):
	def setUp(self):
		for doctype in ["Attendance Request", "Attendance"]:
			frappe.db.delete(doctype)

		from_date = get_year_start(add_months(getdate(), -1))
		to_date = get_year_ending(getdate())
		self.holiday_list = make_holiday_list(
			from_date=from_date, to_date=to_date, add_weekly_offs=False
		)

		self.employee = get_employee()
		frappe.db.set_value("Employee", self.employee.name, "holiday_list", self.holiday_list)

	def test_on_duty_attendance_request(self):
		"Test creation of Attendance from Attendance Request, on duty."
		attendance_request = create_attendance_request(
			employee=self.employee.name, reason="On Duty", company="_Test Company"
		)
		records = self.get_attendance_records(attendance_request.name)

		self.assertEqual(len(records), 2)
		self.assertEqual(records[0].status, "Present")
		self.assertEqual(records[0].docstatus, 1)

		# cancelling attendance request cancels linked attendances
		attendance_request.cancel()

		# cancellation alters docname
		# fetch attendance value again to avoid stale docname
		records = self.get_attendance_records(attendance_request.name)
		self.assertEqual(records[0].docstatus, 2)

	def test_work_from_home_attendance_request(self):
		"Test creation of Attendance from Attendance Request, work from home."
		attendance_request = create_attendance_request(
			employee=self.employee.name, reason="Work From Home", company="_Test Company"
		)
		records = self.get_attendance_records(attendance_request.name)

		self.assertEqual(records[0].status, "Work From Home")

		# cancelling attendance request cancels linked attendances
		attendance_request.cancel()
		records = self.get_attendance_records(attendance_request.name)
		self.assertEqual(records[0].docstatus, 2)

	def test_overwrite_attendance(self):
		attendance_name = mark_attendance(self.employee.name, getdate(), "Absent")

		attendance_request = create_attendance_request(
			employee=self.employee.name, reason="Work From Home", company="_Test Company"
		)
		prev_attendance = frappe.get_doc("Attendance", attendance_name)

		# attendance request should overwrite attendance status from Absent to Work From Home
		self.assertEqual(prev_attendance.status, "Work From Home")
		self.assertEqual(prev_attendance.attendance_request, attendance_request.name)

	def test_skip_attendance_on_holiday(self):
		today = getdate()
		holiday_list = frappe.get_doc("Holiday List", self.holiday_list)
		holiday_list.append(
			"holidays",
			{
				"holiday_date": today,
				"description": "Test Holiday",
			},
		)
		holiday_list.save()

		attendance_request = create_attendance_request(
			employee=self.employee.name, reason="On Duty", company="_Test Company"
		)

		records = self.get_attendance_records(attendance_request.name)
		# only 1 attendance marked for yesterday
		# attendance skipped for today since its a holiday
		self.assertEqual(len(records), 1)
		self.assertEqual(records[0].status, "Present")

	def get_attendance_records(self, attendance_request: str) -> list[dict]:
		return frappe.db.get_all(
			"Attendance",
			{
				"attendance_request": attendance_request,
			},
			["status", "docstatus"],
		)


def get_employee():
	return frappe.get_doc("Employee", "_T-Employee-00001")


def create_attendance_request(**args: dict) -> dict:
	args = frappe._dict(args)
	today = getdate()

	attendance_request = frappe.get_doc(
		{
			"doctype": "Attendance Request",
			"employee": args.employee or get_employee().name,
			"from_date": add_days(today, -1),
			"to_date": today,
			"reason": "On Duty",
			"company": "_Test Company",
		}
	)

	if args:
		attendance_request.update(args)

	return attendance_request.submit()
