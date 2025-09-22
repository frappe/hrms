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
		# test payroll correction for earnings and accruals, ensure additional salary and employee benefit ledger entries are created\

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

		arrear_doc = frappe.get_doc(
			{
				"doctype": "Payroll Correction",
				"employee": emp,
				"payroll_period": payroll_period.name,
				"payroll_date": add_days(payroll_period.start_date, 32),  # next month
				"company": "_Test Company",
				"days_to_reverse": 1,
				"month_for_lwp_reversal": calendar.month_name[payroll_period.start_date.month],
				"salary_slip_reference": salary_slip.name,
				"working_days": 27,
				"lwp_days": 1,
				"total_lwp_applied": 1,
			}
		).save()
		arrear_doc.submit()

		basic_salary_arrear = (65000 / 27) * 1
		mediclaim_allowance_arrear = (24000 / 12 / 27) * 1
		self.assertEqual(arrear_doc.get("earning_arrears")[0].amount, flt(basic_salary_arrear, 2))
		self.assertEqual(arrear_doc.get("accrual_arrears")[0].amount, flt(mediclaim_allowance_arrear, 2))
		self.assertTrue(
			frappe.db.exists(
				"Additional Salary",
				{
					"ref_docname": arrear_doc.name,
				},
			)
		)
		self.assertTrue(
			frappe.db.exists(
				"Employee Benefit Ledger",
				{
					"reference_document": arrear_doc.name,
				},
			)
		)
