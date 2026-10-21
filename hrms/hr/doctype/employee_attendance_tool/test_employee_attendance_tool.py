# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, getdate

from erpnext.setup.doctype.employee.employee import is_holiday
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
from hrms.hr.doctype.shift_type.test_shift_type import make_shift_assignment, setup_shift_type
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_leave_application
from hrms.tests.utils import HRMSTestSuite, make_company_restricted_user


class TestEmployeeAttendanceTool(HRMSTestSuite):
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
		date = getdate()
		while is_holiday(employee=employee.name, date=date):
			date = add_days(date, -1)
		frappe.get_doc(
			{
				"doctype": "Leave Allocation",
				"employee": employee.name,
				"employee_name": employee.employee_name,
				"leave_type": leave_type.name,
				"from_date": add_days(date, -2),
				"new_leaves_allocated": 15,
				"carry_forward": 0,
				"to_date": add_days(getdate(), 30),
			}
		).submit()
		make_leave_application(
			employee=employee.name,
			from_date=date,
			to_date=date,
			leave_type=leave_type.name,
			half_day=1,
			half_day_date=date,
		)
		mark_attendance(self.employee2, attendance_date=date, status="Half Day", half_day_status="Absent")
		total_employees = get_employees(date, company="_Test Company")
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
		while is_holiday(employee=employee2.name, date=date) or is_holiday(
			employee=employee4.name, date=date
		):
			date = add_days(date, -1)
		create_leave_allocation(employee2, leave_type, date)
		create_leave_allocation(employee4, leave_type, date)
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
				"company": "_Test Company",
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
				"company": "_Test Company",
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
				"company": "_Test Company",
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
		).submit()
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

	def test_mark_attendance_outside_company_scope(self):
		user = make_company_restricted_user("test_scoped_hr_user@example.com", "_Test Company")

		date = add_days(getdate(), -1)
		while is_holiday(employee=self.employee4, date=date):
			date = add_days(date, -1)

		frappe.set_user(user)
		try:
			# employee4 belongs to _Test Company 1, outside the user's scope
			with self.assertRaises(frappe.PermissionError):
				mark_employee_attendance(employee_list=[self.employee4], status="Present", date=date)

			with self.assertRaises(frappe.PermissionError):
				mark_employee_attendance(
					employee_list=[],
					status="Present",
					date=date,
					mark_half_day=True,
					half_day_status="Absent",
					half_day_employee_list=[self.employee4],
				)

			# employee3 belongs to _Test Company but the caller claims a different company
			with self.assertRaises(frappe.ValidationError):
				mark_employee_attendance(
					employee_list=[self.employee3], status="Present", date=date, company="_Test Company 1"
				)
		finally:
			frappe.set_user("Administrator")

		self.assertFalse(
			frappe.db.exists("Attendance", {"employee": self.employee4, "attendance_date": date})
		)
		self.assertFalse(
			frappe.db.exists("Attendance", {"employee": self.employee3, "attendance_date": date})
		)

	def test_mark_attendance_rejects_non_string_employees(self):
		date = add_days(getdate(), -1)
		for bad_list in ([None], [1], [{"name": self.employee1}], [self.employee1, ""]):
			self.assertRaises(
				frappe.ValidationError,
				mark_employee_attendance,
				employee_list=bad_list,
				status="Present",
				date=date,
			)
		self.assertFalse(frappe.db.exists("Attendance", {"attendance_date": date}))

	def test_half_day_update_requires_write_access_on_each_record(self):
		hr_user = make_company_restricted_user("test_half_day_writer@example.com", "_Test Company 1")

		date = add_days(getdate(), -1)
		while is_holiday(employee=self.employee1, date=date):
			date = add_days(date, -1)

		attendance = make_half_day_leave_attendance(self.employee1, date)

		# employee1 sits outside the user's company scope; share the records read-only so
		# they are visible to the user without being editable
		frappe.share.add("Employee", self.employee1, hr_user, read=1)
		frappe.share.add("Attendance", attendance.name, hr_user, read=1)

		def mark_half_day():
			mark_employee_attendance(
				employee_list=[],
				status="Present",
				date=date,
				mark_half_day=True,
				half_day_status="Absent",
				half_day_employee_list=[self.employee1],
			)

		frappe.set_user(hr_user)
		try:
			self.assertRaises(frappe.PermissionError, mark_half_day)
		finally:
			frappe.set_user("Administrator")

		attendance.reload()
		self.assertEqual(attendance.half_day_status, "Present")

		frappe.share.add("Attendance", attendance.name, hr_user, read=1, write=1)
		frappe.set_user(hr_user)
		try:
			mark_half_day()
		finally:
			frappe.set_user("Administrator")

		attendance.reload()
		self.assertEqual(attendance.half_day_status, "Absent")

	def test_mark_half_day_attendance_permissions(self):
		user_no_role = "test_no_role@example.com"

		frappe.set_user("Administrator")
		make_employee(user_no_role, company="_Test Company")

		date = add_days(getdate(), -1)
		while is_holiday(employee=self.employee1, date=date):
			date = add_days(date, -1)

		# Create and submit an attendance record as Administrator
		attendance = make_half_day_leave_attendance(self.employee1, date)

		# Scenario 1 (Security): user without Attendance write permission
		# Verify the unauthorized user cannot update half-day attendance
		frappe.set_user(user_no_role)
		try:
			# Precondition: verify the user lacks doctype-level write access
			self.assertFalse(frappe.has_permission("Attendance", "write"))

			with self.assertRaises(frappe.PermissionError):
				mark_employee_attendance(
					employee_list=[],
					status="Present",
					date=date,
					mark_half_day=True,
					half_day_status="Absent",
					half_day_employee_list=[self.employee1],
				)
		finally:
			frappe.set_user("Administrator")

		# Verify the record was NOT modified
		attendance.reload()
		self.assertEqual(attendance.half_day_status, "Present")
		self.assertEqual(attendance.status, "Half Day")

		# Scenario 2 (Positive): Administrator can update half-day attendance
		mark_employee_attendance(
			employee_list=[],
			status="Present",
			date=date,
			mark_half_day=True,
			half_day_status="Absent",
			half_day_employee_list=[self.employee1],
		)

		attendance.reload()
		self.assertEqual(attendance.half_day_status, "Absent")
		self.assertEqual(attendance.status, "Half Day")

	def test_half_day_update_only_touches_half_day_leave_attendance(self):
		shift = setup_shift_type(shift_type="Shift 1", start_time="08:00:00", end_time="10:00:00")
		date = add_days(getdate(), -1)
		present = mark_attendance(self.employee1, date, "Present", shift=shift.name)
		half_day = make_half_day_leave_attendance(self.employee2, date, shift=shift.name)

		self.assertRaises(
			frappe.ValidationError,
			mark_employee_attendance,
			employee_list=[],
			status="Present",
			date=date,
			mark_half_day=True,
			half_day_status="Bogus",
			half_day_employee_list=[self.employee2],
		)

		mark_employee_attendance(
			employee_list=[],
			status="Present",
			date=date,
			mark_half_day=True,
			half_day_status="Absent",
			half_day_employee_list=[self.employee1, self.employee2],
		)

		present = frappe.db.get_value(
			"Attendance", present, ["status", "half_day_status", "shift"], as_dict=True
		)
		self.assertEqual(present.status, "Present")
		self.assertIsNone(present.half_day_status)
		self.assertEqual(present.shift, shift.name)

		half_day.reload()
		self.assertEqual(half_day.half_day_status, "Absent")
		self.assertEqual(half_day.shift, shift.name)

	def test_marked_attendance_respects_filters(self):
		date = add_days(getdate(), -1)
		mark_attendance(self.employee1, date, "Present")
		mark_attendance(self.employee4, date, "Present")

		marked = [d.employee for d in get_employees(date, company="_Test Company")["marked"]]
		self.assertIn(self.employee1, marked)
		self.assertNotIn(self.employee4, marked)

	def test_shift_filter_ignores_invalid_assignments(self):
		shift = setup_shift_type(shift_type="Shift 1", start_time="08:00:00", end_time="10:00:00")
		other_shift = setup_shift_type(shift_type="Shift 2", start_time="11:00:00", end_time="13:00:00")
		date = getdate()
		frappe.db.set_value("Employee", self.employee3, "default_shift", shift.name)

		make_shift_assignment(shift.name, self.employee1, add_days(date, -10), add_days(date, -1))
		make_shift_assignment(shift.name, self.employee2, add_days(date, -10), do_not_submit=True)
		make_shift_assignment(other_shift.name, self.employee3, add_days(date, -10))

		unmarked = [{"employee": e} for e in (self.employee1, self.employee2, self.employee3)]
		self.assertEqual(_get_unmarked_attendance_with_shift(unmarked, shift.name, date), [])


def make_half_day_leave_attendance(employee, date, shift=None):
	leave_type = create_leave_type(leave_type="_Test Employee Attendance Tool", include_holidays=0)
	attendance = frappe.get_doc(
		{
			"doctype": "Attendance",
			"employee": employee,
			"attendance_date": date,
			"status": "Half Day",
			"leave_type": leave_type.name,
			"half_day_status": "Present",
			"modify_half_day_status": 1,
			"shift": shift,
			"company": frappe.db.get_value("Employee", employee, "company"),
		}
	)
	attendance.flags.ignore_validate = True
	attendance.insert()
	attendance.submit()
	return attendance


def create_leave_allocation(employee, leave_type, date=None):
	from_date = add_days(date or getdate(), -2)
	frappe.get_doc(
		{
			"doctype": "Leave Allocation",
			"employee": employee.name,
			"employee_name": employee.employee_name,
			"leave_type": leave_type.name,
			"from_date": from_date,
			"new_leaves_allocated": 15,
			"carry_forward": 0,
			"to_date": add_days(getdate(), 30),
		}
	).submit()
