# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
import calendar

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, flt

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip


class TestPayrollCorrection(IntegrationTestCase):
	def test_payroll_correction(self):
		from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure
		# test payroll correction, ensure additional salary and employee benefit ledger entries are created\

		frappe.db.set_single_value("Payroll Settings", "payroll_based_on", "Leave")

		emp = make_employee(
			"test_payroll_correction@salary.com",
			company="_Test Company",
			date_of_joining="2021-01-01",
		)
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
