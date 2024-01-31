# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, add_months, today

from hrms.hr.doctype.attendance_request.test_attendance_request import get_employee
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on
from hrms.hr.doctype.leave_period.test_leave_period import create_leave_period
from hrms.tests.test_utils import add_date_to_holiday_list

test_dependencies = ["Employee"]


class TestCompensatoryLeaveRequest(FrappeTestCase):
	def setUp(self):
		frappe.db.delete("Compensatory Leave Request")
		frappe.db.delete("Leave Ledger Entry")
		frappe.db.delete("Leave Allocation")
		frappe.db.delete("Attendance")
		frappe.db.delete("Leave Period")

		create_leave_period(add_months(today(), -3), add_months(today(), 3), "_Test Company")
		create_holiday_list()

		employee = get_employee()
		employee.holiday_list = "_Test Compensatory Leave"
		employee.save()

	def test_leave_balance_on_submit(self):
		"""check creation of leave allocation on submission of compensatory leave request"""
		employee = get_employee()
		mark_attendance(employee)
		compensatory_leave_request = get_compensatory_leave_request(employee.name)

		before = get_leave_balance_on(employee.name, compensatory_leave_request.leave_type, today())
		compensatory_leave_request.submit()

		self.assertEqual(
			get_leave_balance_on(
				employee.name, compensatory_leave_request.leave_type, add_days(today(), 1)
			),
			before + 1,
		)

	def test_leave_allocation_update_on_submit(self):
		employee = get_employee()
		mark_attendance(employee, date=add_days(today(), -1))
		compensatory_leave_request = get_compensatory_leave_request(
			employee.name, leave_date=add_days(today(), -1)
		)
		compensatory_leave_request.submit()

		# leave allocation creation on submit
		leaves_allocated = frappe.db.get_value(
			"Leave Allocation",
			{"name": compensatory_leave_request.leave_allocation},
			["total_leaves_allocated"],
		)
		self.assertEqual(leaves_allocated, 1)

		mark_attendance(employee)
		compensatory_leave_request = get_compensatory_leave_request(employee.name)
		compensatory_leave_request.submit()

		# leave allocation updates on submission of second compensatory leave request
		leaves_allocated = frappe.db.get_value(
			"Leave Allocation",
			{"name": compensatory_leave_request.leave_allocation},
			["total_leaves_allocated"],
		)
		self.assertEqual(leaves_allocated, 2)

	def test_creation_of_leave_ledger_entry_on_submit(self):
		"""check creation of leave ledger entry on submission of leave request"""
		employee = get_employee()
		mark_attendance(employee)
		compensatory_leave_request = get_compensatory_leave_request(employee.name)
		compensatory_leave_request.submit()

		filters = dict(transaction_name=compensatory_leave_request.leave_allocation)
		leave_ledger_entry = frappe.get_all("Leave Ledger Entry", fields="*", filters=filters)

		self.assertEqual(len(leave_ledger_entry), 1)
		self.assertEqual(leave_ledger_entry[0].employee, compensatory_leave_request.employee)
		self.assertEqual(leave_ledger_entry[0].leave_type, compensatory_leave_request.leave_type)
		self.assertEqual(leave_ledger_entry[0].leaves, 1)

		# check reverse leave ledger entry on cancellation
		compensatory_leave_request.cancel()
		leave_ledger_entry = frappe.get_all(
			"Leave Ledger Entry", fields="*", filters=filters, order_by="creation desc"
		)

		self.assertEqual(len(leave_ledger_entry), 2)
		self.assertEqual(leave_ledger_entry[0].employee, compensatory_leave_request.employee)
		self.assertEqual(leave_ledger_entry[0].leave_type, compensatory_leave_request.leave_type)
		self.assertEqual(leave_ledger_entry[0].leaves, -1)

	def test_half_day_compensatory_leave(self):
		employee = get_employee()
		mark_attendance(employee, status="Half Day")
		date = today()
		compensatory_leave_request = frappe.new_doc("Compensatory Leave Request")
		compensatory_leave_request.update(
			dict(
				employee=employee.name,
				leave_type="Compensatory Off",
				work_from_date=date,
				work_end_date=date,
				reason="test",
			)
		)

		# cannot apply for full day compensatory leave for a half day attendance
		self.assertRaises(frappe.ValidationError, compensatory_leave_request.submit)

		compensatory_leave_request.half_day = 1
		compensatory_leave_request.half_day_date = date
		compensatory_leave_request.submit()

		# check creation of leave ledger entry on submission of leave request
		leave_ledger_entry = frappe.get_all(
			"Leave Ledger Entry",
			fields="*",
			filters={"transaction_name": compensatory_leave_request.leave_allocation},
		)

		self.assertEqual(leave_ledger_entry[0].leaves, 0.5)

	def test_request_on_leave_period_boundary(self):
		frappe.db.delete("Leave Period")
		create_leave_period("2023-01-01", "2023-12-31", "_Test Company")

		employee = get_employee()
		boundary_date = "2023-12-31"
		add_date_to_holiday_list(boundary_date, employee.holiday_list)
		mark_attendance(employee, boundary_date, "Present")

		# no leave period found of "2024-01-01"
		compensatory_leave_request = frappe.new_doc("Compensatory Leave Request")
		compensatory_leave_request.update(
			dict(
				employee=employee.name,
				leave_type="Compensatory Off",
				work_from_date=boundary_date,
				work_end_date=boundary_date,
				reason="test",
			)
		)
		self.assertRaises(frappe.ValidationError, compensatory_leave_request.submit)

		create_leave_period("2023-01-01", "2023-12-31", "_Test Company")
		compensatory_leave_request.submit()


def get_compensatory_leave_request(employee, leave_date=today()):
	prev_comp_leave_req = frappe.db.get_value(
		"Compensatory Leave Request",
		dict(
			leave_type="Compensatory Off",
			work_from_date=leave_date,
			work_end_date=leave_date,
			employee=employee,
		),
		"name",
	)
	if prev_comp_leave_req:
		return frappe.get_doc("Compensatory Leave Request", prev_comp_leave_req)

	return frappe.get_doc(
		dict(
			doctype="Compensatory Leave Request",
			employee=employee,
			leave_type="Compensatory Off",
			work_from_date=leave_date,
			work_end_date=leave_date,
			reason="test",
		)
	).insert()


def mark_attendance(employee, date=None, status="Present"):
	if not date:
		date = today()

	if not frappe.db.exists(
		dict(doctype="Attendance", employee=employee.name, attendance_date=date, status="Present")
	):
		attendance = frappe.get_doc(
			{"doctype": "Attendance", "employee": employee.name, "attendance_date": date, "status": status}
		)
		attendance.save()
		attendance.submit()


def create_holiday_list():
	if frappe.db.exists("Holiday List", "_Test Compensatory Leave"):
		return

	holiday_list = frappe.get_doc(
		{
			"doctype": "Holiday List",
			"from_date": add_months(today(), -3),
			"to_date": add_months(today(), 3),
			"holidays": [
				{"description": "Test Holiday", "holiday_date": today()},
				{"description": "Test Holiday 1", "holiday_date": add_days(today(), -1)},
			],
			"holiday_list_name": "_Test Compensatory Leave",
		}
	)
	holiday_list.save()
