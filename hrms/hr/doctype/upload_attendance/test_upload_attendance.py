# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import getdate

import erpnext
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.holiday_list_assignment.test_holiday_list_assignment import (
	create_holiday_list_assignment,
)
from hrms.hr.doctype.upload_attendance.upload_attendance import get_data
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_holiday_list
from hrms.tests.test_utils import add_date_to_holiday_list
from hrms.tests.utils import HRMSTestSuite


class TestUploadAttendance(HRMSTestSuite):
	def setUp(self):
		frappe.db.set_value("Company", "_Test Company", "default_holiday_list", "_Test Holiday List")

	def test_date_range(self):
		employee = make_employee("test_employee@company.com", company="_Test Company")
		employee_doc = frappe.get_doc("Employee", employee)
		date_of_joining = "2018-01-02"
		relieving_date = "2018-01-03"
		from_date = "2018-01-01"
		to_date = "2018-01-04"
		holiday_list = make_holiday_list(
			"Test Upload Attendance Company HLA 2018",
			from_date="2018-01-01",
			to_date="2018-12-31",
		)
		create_holiday_list_assignment(
			"Company", assigned_to="_Test Company", holiday_list=holiday_list, from_date=from_date
		)
		employee_doc.date_of_joining = date_of_joining
		employee_doc.relieving_date = relieving_date
		employee_doc.save()
		args = {"from_date": from_date, "to_date": to_date}
		data = get_data(args)
		filtered_data = []
		for row in data:
			if row[1] == employee:
				filtered_data.append(row)
		for row in filtered_data:
			self.assertTrue(
				getdate(row[3]) >= getdate(date_of_joining) and getdate(row[3]) <= getdate(relieving_date)
			)

	def test_template_uses_business_date_holiday_list(self):
		employee = make_employee("test_upload_attendance_hla_as_on@example.com", company="_Test Company")
		employee_doc = frappe.get_doc("Employee", employee)
		employee_doc.date_of_joining = "2026-01-01"
		employee_doc.relieving_date = None
		employee_doc.save()

		holiday_list_a = make_holiday_list(
			"Test Upload Attendance HLA A",
			from_date="2026-01-01",
			to_date="2026-01-31",
			add_weekly_offs=False,
		)
		holiday_list_b = make_holiday_list(
			"Test Upload Attendance HLA B",
			from_date="2026-01-01",
			to_date="2026-12-31",
			add_weekly_offs=False,
		)
		add_date_to_holiday_list("2026-01-01", holiday_list_a)
		add_date_to_holiday_list("2026-01-02", holiday_list_b)
		create_holiday_list_assignment(
			"Employee", assigned_to=employee, holiday_list=holiday_list_a, from_date="2026-01-01"
		)
		create_holiday_list_assignment(
			"Employee", assigned_to=employee, holiday_list=holiday_list_b, from_date="2026-06-01"
		)

		data = get_data({"from_date": "2026-01-01", "to_date": "2026-01-01"})
		employee_rows = [row for row in data if row[1] == employee]

		self.assertEqual(len(employee_rows), 1)
		self.assertEqual(employee_rows[0][4], "Holiday")
