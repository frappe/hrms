# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, flt, getdate, nowdate, today

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.employee_checkin.test_employee_checkin import make_checkin
from hrms.hr.doctype.overtime_type.test_overtime_type import create_overtime_type
from hrms.hr.doctype.shift_type.test_shift_type import make_shift_assignment, setup_shift_type
from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure

TEST_COMPANY = "_Test Company"


class TestOvertimeSlip(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("Overtime Type")
		frappe.db.delete("Shift Type", {"name": "_Test Overtime Shift"})

	def test_overtime_calculation_and_additional_salary_creation(self):
		from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip

		employee = make_employee("test_overtime_slip_salary@example.com")
		salary_structure = make_salary_structure(
			"Test Overtime Salary Slip", "Monthly", employee=employee, company=TEST_COMPANY
		)
		overtime_type, overtime_slip, total_overtime_hours = setup_overtime(employee)

		attendance_records = frappe.get_all(
			"Attendance",
			filters={"employee": employee, "status": "Present"},
			fields=["name", "actual_overtime_duration", "overtime_type", "attendance_date"],
		)

		records = {rec.name: rec for rec in attendance_records}

		for detail in overtime_slip.overtime_details:
			self.assertIn(detail.reference_document, records)
			self.assertEqual(
				detail.overtime_duration, records[detail.reference_document].actual_overtime_duration
			)
			self.assertEqual(str(detail.date), str(records[detail.reference_document].attendance_date))

		salary_slip = make_salary_slip(
			salary_structure.name,
			employee=employee,
			posting_date=overtime_slip.start_date,
		)

		standard_working_hours = overtime_slip.overtime_details[0].standard_working_hours

		applicable_amount = sum(
			[
				data.amount
				for data in salary_slip.earnings
				if data.salary_component in ["Basic Salary"] and not data.get("additional_salary", None)
			]
		)
		daily_wages = applicable_amount / salary_slip.payment_days
		hourly_rate = daily_wages / standard_working_hours
		expected_overtime_amount = hourly_rate * total_overtime_hours * overtime_type.standard_multiplier

		actual_overtime_amount = frappe.db.get_value(
			"Additional Salary", {"ref_docname": overtime_slip.name}, "amount"
		)
		self.assertEqual(flt(expected_overtime_amount, 2), actual_overtime_amount)

	def test_overtime_calculation_for_fixed_hourly_rate(self):
		employee = make_employee("test_overtime_slip_fixed@example.com")
		make_salary_structure("Test Overtime Salary Slip", "Monthly", employee=employee, company=TEST_COMPANY)

		overtime_type, overtime_slip, total_overtime_hours = setup_overtime(employee, "Fixed Hourly Rate")
		expected_overtime_amount = (
			overtime_type.hourly_rate * total_overtime_hours * overtime_type.standard_multiplier
		)

		actual_overtime_amount = frappe.db.get_value(
			"Additional Salary", {"ref_docname": overtime_slip.name}, "amount"
		)

		self.assertEqual(flt(expected_overtime_amount, 2), flt(actual_overtime_amount, 2))

	def test_overtime_slip_creation_via_payroll_entry(self):
		"""Test creation of overtime slips via payroll entry."""
		from hrms.payroll.doctype.payroll_entry.payroll_entry import get_start_end_dates
		from hrms.payroll.doctype.payroll_entry.test_payroll_entry import get_payroll_entry

		company = frappe.get_doc("Company", TEST_COMPANY)
		employee = make_employee("test_overtime_slip_01@example.com")
		overtime_type = create_overtime_type(overtime_calculation_method="Fixed Hourly Rate")
		shift_type = setup_shift_type(
			company=TEST_COMPANY,
			shift_type="_Test Overtime Shift",
			allow_overtime=1,
			overtime_type=overtime_type.name,
			last_sync_of_checkin=f"{add_days(getdate(), 1)} 15:00:00",
			mark_auto_attendance_on_holidays=1,
		)
		frappe.db.set_single_value("Payroll Settings", "create_overtime_slip", 1)

		make_salary_structure("Test Overtime Salary Slip", "Monthly", employee=employee, company=TEST_COMPANY)
		make_shift_assignment(shift_type=shift_type.name, employee=employee, start_date=add_days(today(), -5))
		create_checkin_records_for_overtime(employee)
		shift_type.process_auto_attendance()

		dates = get_start_end_dates("Monthly", nowdate())
		payroll_entry = get_payroll_entry(
			start_date=dates.start_date,
			end_date=dates.end_date,
			payable_account=company.default_payroll_payable_account,
			currency=company.default_currency,
			company=company.name,
		)

		payroll_entry.create_overtime_slips()
		payroll_entry.submit_overtime_slips()

		overtime_slip = frappe.db.get_value(
			"Overtime Slip",
			{
				"employee": employee,
				"payroll_entry": payroll_entry.name,
			},
			["docstatus"],
			as_dict=1,
		)

		self.assertTrue(overtime_slip)
		self.assertEqual(overtime_slip.docstatus, 1)

	def tearDown(self):
		frappe.db.rollback()


def create_overtime_slip(employee):
	slip = frappe.new_doc("Overtime Slip")
	slip.employee = employee
	slip.posting_date = today()
	slip.start_date = add_days(getdate(), -2)
	slip.end_date = add_days(getdate(), 2)
	slip.get_emp_and_overtime_details()
	return slip


def create_checkin_records_for_overtime(employee):
	yesterday = add_days(getdate(), -1)
	checkin_times = [
		(f"{yesterday} 7:00:00", "IN"),
		(f"{yesterday} 13:00:00", "OUT"),
		(f"{getdate()} 7:00:00", "IN"),
		(f"{getdate()} 13:00:00", "OUT"),
	]
	for time, log_type in checkin_times:
		make_checkin(employee, time=time, log_type=log_type)


def setup_overtime(employee, overtime_calculation_method="Salary Component Based"):
	overtime_type = create_overtime_type(overtime_calculation_method=overtime_calculation_method)

	shift_type = setup_shift_type(
		company=TEST_COMPANY,
		shift_type="_Test Overtime Shift",
		allow_overtime=1,
		overtime_type=overtime_type.name,
		last_sync_of_checkin=f"{add_days(getdate(), 1)} 15:00:00",
		mark_auto_attendance_on_holidays=1,
	)

	make_shift_assignment(shift_type=shift_type.name, employee=employee, start_date=add_days(today(), -5))
	create_checkin_records_for_overtime(employee)
	shift_type.process_auto_attendance()

	slip = create_overtime_slip(employee)
	slip.submit()

	overtime_details = frappe.get_all(
		"Overtime Details",
		filters={"parent": slip.name},
		fields=["overtime_type", "overtime_duration", "date", "standard_working_hours"],
	)

	total_overtime_hours = sum(detail["overtime_duration"] for detail in overtime_details)

	return overtime_type, slip, total_overtime_hours
