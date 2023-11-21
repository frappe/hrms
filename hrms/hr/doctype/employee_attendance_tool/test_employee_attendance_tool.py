# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.attendance.attendance import mark_attendance
from hrms.hr.doctype.employee_attendance_tool.employee_attendance_tool import (
	get_employees,
	mark_employee_attendance,
)
from hrms.hr.doctype.shift_type.test_shift_type import setup_shift_type


class TestEmployeeAttendanceTool(FrappeTestCase):
	def setUp(self):
		frappe.db.delete("Attendance")

		self.employee1 = make_employee("test_present@example.com", company="_Test Company")
		self.employee2 = make_employee("test_absent@example.com", company="_Test Company")
		self.employee3 = make_employee("test_unmarked@example.com", company="_Test Company")

		self.employee4 = make_employee("test_filter@example.com", company="_Test Company 1")

	def test_get_employee_attendance(self):
		date = getdate("28-02-2023")
		mark_attendance(self.employee1, date, "Present")
		mark_attendance(self.employee2, date, "Absent")

		employees = get_employees(date, company="_Test Company")

		marked_employees = employees["marked"]
		unmarked_employees = [entry.employee for entry in employees["unmarked"]]

		# absent
		self.assertEqual(marked_employees[0].get("employee"), self.employee2)
		# present
		self.assertEqual(marked_employees[1].get("employee"), self.employee1)
		# unmarked
		self.assertIn(self.employee3, unmarked_employees)
		# employee from a different company
		self.assertNotIn(self.employee4, unmarked_employees)

	def test_mark_employee_attendance(self):
		shift = setup_shift_type(shift_type="Shift 1", start_time="08:00:00", end_time="10:00:00")
		date = getdate("28-02-2023")

		mark_employee_attendance(
			[self.employee1, self.employee2],
			"Present",
			date,
			shift=shift.name,
			late_entry=1,
		)

		attendance = frappe.db.get_value(
			"Attendance",
			{"employee": self.employee1, "attendance_date": date},
			["status", "shift", "late_entry"],
			as_dict=True,
		)

		self.assertEqual(attendance.status, "Present")
		self.assertEqual(attendance.shift, shift.name)
		self.assertEqual(attendance.late_entry, 1)
