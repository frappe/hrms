# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, add_months, get_year_ending, get_year_start, getdate

from hrms.hr.doctype.attendance.attendance import mark_attendance
from hrms.hr.doctype.attendance_request.attendance_request import OverlappingAttendanceRequestError
from hrms.hr.doctype.leave_application.test_leave_application import make_allocation_record
from hrms.payroll.doctype.salary_slip.test_salary_slip import (
	make_holiday_list,
	make_leave_application,
)
from hrms.tests.test_utils import get_first_sunday

test_dependencies = ["Employee"]


class TestAttendanceRequest(FrappeTestCase):
	def setUp(self):
		for doctype in ["Attendance Request", "Attendance"]:
			frappe.db.delete(doctype)

		self.from_date = get_year_start(add_months(getdate(), -1))
		self.to_date = get_year_ending(getdate())
		self.holiday_list = make_holiday_list(
			from_date=self.from_date, to_date=self.to_date, add_weekly_offs=False
		)

		self.employee = get_employee()
		frappe.db.set_value("Employee", self.employee.name, "holiday_list", self.holiday_list)

	def test_attendance_request_overlap(self):
		create_attendance_request(employee=self.employee.name, reason="On Duty", company="_Test Company")

		today = getdate()
		dateranges = [
			(add_days(today, -2), today),
			(today, today),
			(today, add_days(today, 1)),
			(add_days(today, -2), add_days(today, 2)),
		]
		attendance_request = frappe.get_doc(
			{
				"doctype": "Attendance Request",
				"employee": self.employee.name,
				"reason": "On Duty",
				"company": "_Test Company",
			}
		)

		for entry in dateranges:
			attendance_request.from_date = entry[0]
			attendance_request.to_date = entry[1]
			self.assertRaises(OverlappingAttendanceRequestError, attendance_request.save)

		# no overlap
		attendance_request.from_date = add_days(today, -3)
		attendance_request.to_date = add_days(today, -2)
		attendance_request.save()

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

	def test_skip_attendance_on_leave(self):
		frappe.delete_doc_if_exists("Leave Type", "Test Skip Attendance", force=1)
		leave_type = frappe.get_doc(
			dict(leave_type_name="Test Skip Attendance", doctype="Leave Type")
		).insert()

		make_allocation_record(
			leave_type=leave_type.name, from_date=self.from_date, to_date=self.to_date
		)
		today = getdate()
		make_leave_application(self.employee.name, today, add_days(today, 1), leave_type.name)

		attendance_request = create_attendance_request(
			employee=self.employee.name, reason="On Duty", company="_Test Company"
		)
		records = self.get_attendance_records(attendance_request.name)

		# only 1 attendance marked for yesterday
		# attendance skipped for today since its a leave
		self.assertEqual(len(records), 1)
		self.assertEqual(records[0].attendance_date, add_days(today, -1))
		self.assertEqual(records[0].status, "Present")

	def get_attendance_records(self, attendance_request: str) -> list[dict]:
		return frappe.db.get_all(
			"Attendance",
			{
				"attendance_request": attendance_request,
			},
			["status", "docstatus", "attendance_date"],
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
