# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.employee_tax_exemption_declaration.test_employee_tax_exemption_declaration import (
	create_payroll_period,
)
from hrms.tests.utils import HRMSTestSuite


class TestEmployeeOtherIncome(HRMSTestSuite):
	def test_company_must_match_employee_and_payroll_period(self):
		employee = make_employee("employee@otherincome.com", company="_Test Company")
		payroll_period = create_payroll_period(company="_Test Company")

		def make_other_income(company):
			return frappe.get_doc(
				{
					"doctype": "Employee Other Income",
					"employee": employee,
					"payroll_period": payroll_period.name,
					"company": company,
					"amount": 10000,
				}
			)

		self.assertRaises(frappe.ValidationError, make_other_income("_Test Company 1").insert)
		make_other_income("_Test Company").insert()
