# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
import calendar
from unittest.mock import patch

import frappe
from frappe import ValidationError
from frappe.utils import add_days, flt

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.salary_slip.test_salary_slip import (
	make_payroll_period,
)
from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
from hrms.payroll.doctype.salary_structure.test_salary_structure import create_salary_structure_assignment
from hrms.tests.utils import HRMSTestSuite


class TestPayrollCorrection(HRMSTestSuite):
	def test_payroll_correction(self):
		from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure
		# test payroll correction, ensure additional salary and employee benefit ledger entries are created\

		frappe.db.set_single_value("Payroll Settings", "payroll_based_on", "Leave")

		emp = make_employee(
			"test_payroll_correction@salary.com",
			company="_Test Company",
			date_of_joining="2021-01-01",
		)
		make_payroll_period(company="_Test Company")
		payroll_period = frappe.get_last_doc("Payroll Period", filters={"company": "_Test Company"})
		salary_structure_doc = make_salary_structure(
			"Test Payroll Correction",
			"Monthly",
			company="_Test Company",
			employee=emp,
			payroll_period=payroll_period,
			test_arrear=True,
			include_flexi_benefits=True,
			base=65000,
		)

		leave_application = frappe.get_doc(
			{
				"doctype": "Leave Application",
				"employee": emp,
				"leave_type": "Leave Without Pay",
				"from_date": payroll_period.start_date,
				"to_date": payroll_period.start_date,
				"company": "_Test Company",
				"status": "Approved",
				"leave_approver": "test@example.com",
			}
		).insert()
		leave_application.submit()

		salary_slip = make_salary_slip(
			salary_structure_doc.name, employee=emp, posting_date=payroll_period.start_date
		)
		salary_slip.save()
		salary_slip.submit()

		payroll_correction_doc = frappe.get_doc(
			{
				"doctype": "Payroll Correction",
				"employee": emp,
				"payroll_period": payroll_period.name,
				"payroll_date": add_days(payroll_period.start_date, 32),  # next month
				"company": "_Test Company",
				"days_to_reverse": 1,
				"month_for_lwp_reversal": calendar.month_name[payroll_period.start_date.month],
				"salary_slip_reference": salary_slip.name,
				"working_days": salary_slip.total_working_days,
				"payment_days": salary_slip.payment_days,
				"lwp_days": salary_slip.leave_without_pay,
			}
		).save()
		payroll_correction_doc.submit()

		earning_arrears = {row.salary_component: row.amount for row in payroll_correction_doc.earning_arrears}
		accrual_arrears = {row.salary_component: row.amount for row in payroll_correction_doc.accrual_arrears}

		basic_salary_arrear = flt((65000 / 27) * 1, 2)
		self.assertIn("Basic Salary", earning_arrears)
		self.assertEqual(earning_arrears["Basic Salary"], basic_salary_arrear)

		mediclaim_allowance_arrear = flt((24000 / 12 / 27) * 1, 2)
		self.assertIn("Mediclaim Allowance", accrual_arrears)
		self.assertEqual(accrual_arrears["Mediclaim Allowance"], mediclaim_allowance_arrear)

		self.assertTrue(
			frappe.db.exists(
				"Additional Salary",
				{
					"ref_docname": payroll_correction_doc.name,
				},
			)
		)
		self.assertTrue(
			frappe.db.exists(
				"Employee Benefit Ledger",
				{
					"reference_document": payroll_correction_doc.name,
				},
			)
		)

	def test_payroll_correction_with_zero_payment_days(self):
		payroll_correction_doc = frappe.get_doc(
			{
				"doctype": "Payroll Correction",
				"employee": "EMP-0001",
				"payroll_period": "Test Payroll Period",
				"payroll_date": "2025-02-01",
				"company": "_Test Company",
				"days_to_reverse": 1,
				"month_for_lwp_reversal": "January",
				"salary_slip_reference": "SAL-SLIP-ZERO-PAYMENT-DAYS",
			}
		)

		salary_slip = frappe._dict(
			{
				"name": "SAL-SLIP-ZERO-PAYMENT-DAYS",
				"payment_days": 0,
				"total_working_days": 30,
				"earnings": [],
				"deductions": [],
				"accrued_benefits": [
					frappe._dict({"salary_component": "Mediclaim Allowance", "amount": 2000})
				],
			}
		)
		salary_slip.precision = lambda fieldname: 2

		with (
			patch("frappe.get_doc", return_value=salary_slip),
			patch("frappe.db.get_list", return_value=["Mediclaim Allowance"]),
			self.assertRaisesRegex(ValidationError, "zero payment days"),
		):
			payroll_correction_doc.populate_breakup_table()

	def test_salary_slip_reference_and_lwp_limit(self):
		from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure

		frappe.db.set_single_value("Payroll Settings", "payroll_based_on", "Leave")
		make_payroll_period(company="_Test Company")
		payroll_period = frappe.get_last_doc("Payroll Period", filters={"company": "_Test Company"})

		emp = make_employee(
			"test_pc_slip_reference@salary.com", company="_Test Company", date_of_joining="2021-01-01"
		)
		other_emp = make_employee(
			"test_pc_other_employee@salary.com", company="_Test Company", date_of_joining="2021-01-01"
		)
		joiner = make_employee(
			"test_pc_joiner@salary.com",
			company="_Test Company",
			date_of_joining=add_days(payroll_period.start_date, 14),
		)
		salary_structure = make_salary_structure(
			"Test Payroll Correction Slip Reference",
			"Monthly",
			company="_Test Company",
			employee=emp,
			payroll_period=payroll_period,
			test_arrear=True,
			base=65000,
		)
		for employee in (other_emp, joiner):
			create_salary_structure_assignment(
				employee,
				salary_structure.name,
				company="_Test Company",
				from_date=max(
					payroll_period.start_date, frappe.db.get_value("Employee", employee, "date_of_joining")
				),
				base=65000,
			)

		frappe.get_doc(
			{
				"doctype": "Leave Application",
				"employee": emp,
				"leave_type": "Leave Without Pay",
				"from_date": payroll_period.start_date,
				"to_date": payroll_period.start_date,
				"company": "_Test Company",
				"status": "Approved",
				"leave_approver": "test@example.com",
			}
		).insert().submit()

		def submitted_slip(employee):
			slip = make_salary_slip(
				salary_structure.name, employee=employee, posting_date=payroll_period.start_date
			)
			slip.save()
			slip.submit()
			return slip

		def payroll_correction(employee, salary_slip, days):
			return frappe.get_doc(
				{
					"doctype": "Payroll Correction",
					"employee": employee,
					"payroll_period": payroll_period.name,
					"payroll_date": add_days(payroll_period.start_date, 32),
					"company": "_Test Company",
					"days_to_reverse": days,
					"month_for_lwp_reversal": calendar.month_name[payroll_period.start_date.month],
					"salary_slip_reference": salary_slip,
				}
			)

		lwp_slip = submitted_slip(emp)
		self.assertRaises(ValidationError, payroll_correction(other_emp, lwp_slip.name, 1).save)

		# days before joining reduce payment days but are not LWP
		joiner_slip = submitted_slip(joiner)
		self.assertLess(joiner_slip.payment_days, joiner_slip.total_working_days)
		self.assertRaises(ValidationError, payroll_correction(joiner, joiner_slip.name, 1).save)

		payroll_correction(emp, lwp_slip.name, 1).save().submit()
		self.assertRaises(ValidationError, payroll_correction(emp, lwp_slip.name, 1).save)

	def test_payroll_correction_skips_components_not_reduced_by_lwp(self):
		payroll_correction_doc = frappe.get_doc(
			{
				"doctype": "Payroll Correction",
				"employee": "EMP-0001",
				"payroll_period": "Test Payroll Period",
				"payroll_date": "2025-02-01",
				"company": "_Test Company",
				"days_to_reverse": 1,
				"month_for_lwp_reversal": "January",
				"salary_slip_reference": "SAL-SLIP-FIXED-COMPONENT",
			}
		)

		salary_slip = frappe._dict(
			{
				"name": "SAL-SLIP-FIXED-COMPONENT",
				"payment_days": 29,
				"total_working_days": 30,
				"earnings": [
					frappe._dict(
						{
							"salary_component": "Basic Salary",
							"default_amount": 30000,
							"amount": 29000,
						}
					),
					frappe._dict(
						{
							"salary_component": "Fixed Allowance",
							"default_amount": 3000,
							"amount": 3000,
						}
					),
				],
				"deductions": [],
				"accrued_benefits": [],
			}
		)
		salary_slip.precision = lambda fieldname: 2

		with (
			patch("frappe.get_doc", return_value=salary_slip),
			patch(
				"frappe.db.get_list",
				side_effect=lambda *args, **kwargs: [
					c for c in ("Basic Salary", "Fixed Allowance") if c in kwargs["filters"]["name"][1]
				],
			),
		):
			payroll_correction_doc.populate_breakup_table()

		self.assertEqual(
			{row.salary_component: row.amount for row in payroll_correction_doc.earning_arrears},
			{"Basic Salary": 1000.0},
		)
