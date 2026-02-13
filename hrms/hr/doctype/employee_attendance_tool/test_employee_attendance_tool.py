# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.attendance.attendance import mark_attendance
from hrms.hr.doctype.employee_attendance_tool.employee_attendance_tool import (
	_get_unmarked_attendance_with_shift,
	get_employees,
	mark_employee_attendance,
)
from hrms.hr.doctype.holiday_list_assignment.test_holiday_list_assignment import (
	create_holiday_list_assignment,
)
from hrms.hr.doctype.leave_type.test_leave_type import create_leave_type
from hrms.hr.doctype.shift_type.test_shift_type import setup_shift_type
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_leave_application


class TestEmployeeAttendanceTool(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("Attendance")

		self.employee1 = make_employee("test_present@example.com", company="_Test Company")
		self.employee2 = make_employee("test_absent@example.com", company="_Test Company")
		self.employee3 = make_employee("test_unmarked@example.com", company="_Test Company")

		self.employee4 = make_employee("test_filter@example.com", company="_Test Company 1")
		create_holiday_list_assignment("Company", "_Test Company 1")

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

	def test_get_employees_for_half_day_attendance(self):
		# only half day attendance created from leave type should be fetched to update in the tool
		employee = frappe.get_doc("Employee", self.employee1)
		leave_type = create_leave_type(leave_type="_Test Employee Attendance Tool", include_holidays=0)
		frappe.get_doc(
			{
				"doctype": "Leave Allocation",
				"employee": employee.name,
				"employee_name": employee.employee_name,
				"leave_type": leave_type.name,
				"from_date": add_days(getdate(), -2),
				"new_leaves_allocated": 15,
				"carry_forward": 0,
				"to_date": add_days(getdate(), 30),
			}
		).submit()
		make_leave_application(
			employee=employee.name,
			from_date=getdate(),
			to_date=getdate(),
			leave_type=leave_type.name,
			half_day=1,
			half_day_date=getdate(),
		)
		mark_attendance(
			self.employee2, attendance_date=getdate(), status="Half Day", half_day_status="Absent"
		)
		total_employees = get_employees(getdate(), company="_Test Company")
		half_marked_employees = total_employees.get("half_day_marked")
		self.assertEqual(len(half_marked_employees), 1)
		self.assertEqual(half_marked_employees[0].get("employee_name"), employee.employee_name)

	def test_update_half_day_attendance(self):
		shift = setup_shift_type(
			shift_type="Test Attendance Tool", start_time="08:00:00", end_time="12:00:00"
		)
		employee4 = frappe.get_doc("Employee", self.employee4)
		employee2 = frappe.get_doc("Employee", self.employee2)
		leave_type = create_leave_type(leave_type="_Test Employee Attendance Tool", include_holidays=0)
		date = add_days(getdate(), -1)
		create_leave_allocation(employee2, leave_type)
		create_leave_allocation(employee4, leave_type)
		make_leave_application(
			employee=employee2.name,
			from_date=date,
			to_date=date,
			leave_type=leave_type.name,
			half_day=1,
			half_day_date=date,
		)
		make_leave_application(
			employee=employee4.name,
			from_date=date,
			to_date=date,
			leave_type=leave_type.name,
			half_day=1,
			half_day_date=date,
		)

		mark_employee_attendance(
			employee_list=[self.employee1, self.employee3],
			status="Present",
			date=date,
			shift=shift.name,
			late_entry=1,
			early_exit=0,
			mark_half_day=True,
			half_day_status="Present",
			half_day_employee_list=[employee2.name, employee4.name],
		)
		attendances = frappe.get_all(
			"Attendance",
			filters={"attendance_date": date},
			fields=["employee", "status", "half_day_status", "shift", "late_entry", "early_exit"],
		)
		self.assertEqual(len(attendances), 4)
		for attendance in attendances:
			if attendance.get("employee") in (self.employee1, self.employee3):
				self.assertEqual(attendance.status, "Present")
				self.assertIsNone(attendance.half_day_status)
			if attendance.get("employee") in (self.employee2, self.employee4):
				self.assertEqual(attendance.status, "Half Day")
				self.assertEqual(attendance.half_day_status, "Present")
			self.assertEqual(attendance.shift, shift.name)

	def test_get_unmarked_attendance_with_shift(self):
		self.shift = setup_shift_type(shift_type="Shift 1", start_time="08:00:00", end_time="10:00:00")
		self.employee1 = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "Morning Shift Assigned",
				"employee": "EMP001",
				"date_of_birth": "1992-01-01",
				"date_of_joining": "2023-01-01",
				"default_shift": "",
				"gender": "Male",
			}
		).insert()

		self.employee2 = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "Test Default Shift",
				"employee": "EMP002",
				"date_of_birth": "1992-01-01",
				"date_of_joining": "2023-01-01",
				"default_shift": self.shift.name,
				"gender": "Male",
			}
		).insert()

		self.employee3 = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "Test Not Assigned",
				"employee": "EMP003",
				"date_of_birth": "1992-01-01",
				"date_of_joining": "2023-01-01",
				"default_shift": "",
				"gender": "Male",
			}
		).insert()

		# Assign a shift to employee1 via Shift Assignment
		self.shift_assignment = frappe.get_doc(
			{
				"doctype": "Shift Assignment",
				"employee": self.employee1.name,
				"shift_type": self.shift.name,
				"start_date": frappe.utils.getdate("2023-02-28"),
				"end_date": frappe.utils.getdate("2023-03-10"),
			}
		).insert()
		# Prepare the unmarked_attendance sample input
		unmarked_attendance = [
			{"employee": self.employee1.name},
			{"employee": self.employee2.name},
			{"employee": self.employee3.name},
		]

		shift = self.shift.name
		date = "2023-03-01"

		result = _get_unmarked_attendance_with_shift(unmarked_attendance, shift, date)

		# Only employee1 and employee2 have the shift (assigned/default)
		filtered = set([emp["employee"] for emp in result])
		self.assertIn(self.employee1.name, filtered)
		self.assertIn(self.employee2.name, filtered)
		self.assertNotIn(self.employee3.name, filtered)


def create_leave_allocation(employee, leave_type):
	frappe.get_doc(
		{
			"doctype": "Leave Allocation",
			"employee": employee.name,
			"employee_name": employee.employee_name,
			"leave_type": leave_type.name,
			"from_date": add_days(getdate(), -2),
			"new_leaves_allocated": 15,
			"carry_forward": 0,
			"to_date": add_days(getdate(), 30),
		}
	).submit()
