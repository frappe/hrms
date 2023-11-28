import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.employee_tax_exemption_declaration.test_employee_tax_exemption_declaration import (
	create_payroll_period,
)
from hrms.payroll.doctype.salary_slip.test_salary_slip import (
	create_salary_slips_for_payroll_period,
)
from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure
from hrms.payroll.report.income_tax_deductions.income_tax_deductions import execute


class TestIncomeTaxDeductions(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.db.delete("Payroll Period")
		frappe.db.delete("Salary Slip")

		cls.create_records()

	@classmethod
	def tearDownClass(cls):
		frappe.db.rollback()

	@classmethod
	def create_records(cls):
		cls.employee = make_employee(
			"test_tax_deductions@example.com",
			company="_Test Company",
			date_of_joining=getdate("01-10-2021"),
		)

		cls.payroll_period = create_payroll_period(
			name="_Test Payroll Period 1", company="_Test Company"
		)
		salary_structure = make_salary_structure(
			"Monthly Salary Structure Test Income Tax Deduction",
			"Monthly",
			employee=cls.employee,
			company="_Test Company",
			currency="INR",
			payroll_period=cls.payroll_period,
			test_tax=True,
		)

		create_salary_slips_for_payroll_period(
			cls.employee, salary_structure.name, cls.payroll_period, num=1
		)

	def test_report(self):
		filters = frappe._dict({"company": "_Test Company"})

		result = execute(filters)
		posting_date = frappe.db.get_value("Salary Slip", {"employee": self.employee}, "posting_date")
		expected_data = {
			"employee": self.employee,
			"employee_name": "test_tax_deductions@example.com",
			"it_comp": "TDS",
			"posting_date": posting_date,
			"it_amount": 7732.0,
			"gross_pay": 78000.0,
			"pan_number": None,
		}

		self.assertEqual(result[1][0], expected_data)
