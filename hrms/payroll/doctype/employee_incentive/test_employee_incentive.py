# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.salary_component.test_salary_component import create_salary_component
from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure
from hrms.tests.utils import HRMSTestSuite


class TestEmployeeIncentive(HRMSTestSuite):
	def setUp(self):
		self.employee = make_employee("test_employee_incentive@salary.com", company="_Test Company")
		make_salary_structure(
			"Salary Structure Incentive",
			"Monthly",
			employee=self.employee,
			company="_Test Company",
			from_date=add_days(getdate(), -30),
		)
		create_salary_component("Incentive Test Component", type="Earning")

	def make_incentive(self, company="_Test Company"):
		return frappe.get_doc(
			{
				"doctype": "Employee Incentive",
				"employee": self.employee,
				"company": company,
				"currency": "INR",
				"salary_component": "Incentive Test Component",
				"incentive_amount": 7000,
				"payroll_date": getdate(),
			}
		)

	def test_cancel_cancels_additional_salary(self):
		incentive = self.make_incentive()
		incentive.submit()
		additional_salary = frappe.db.get_value(
			"Additional Salary", {"ref_doctype": incentive.doctype, "ref_docname": incentive.name}
		)
		self.assertTrue(additional_salary)

		incentive.cancel()
		self.assertEqual(frappe.db.get_value("Additional Salary", additional_salary, "docstatus"), 2)

	def test_company_must_match_employee(self):
		self.assertRaisesRegex(
			frappe.ValidationError,
			"belongs to company",
			self.make_incentive(company="_Test Company 1").insert,
		)
