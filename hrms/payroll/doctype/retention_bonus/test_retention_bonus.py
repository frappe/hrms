# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.salary_component.test_salary_component import create_salary_component
from hrms.tests.utils import HRMSTestSuite


class TestRetentionBonus(HRMSTestSuite):
	def test_company_must_match_employee(self):
		employee = make_employee("test_retention_bonus@salary.com", company="_Test Company")
		create_salary_component("Retention Bonus Test Component", type="Earning")
		bonus = frappe.get_doc(
			{
				"doctype": "Retention Bonus",
				"employee": employee,
				"company": "_Test Company 1",
				"currency": "INR",
				"salary_component": "Retention Bonus Test Component",
				"bonus_amount": 5000,
				"bonus_payment_date": add_days(getdate(), 10),
			}
		)
		self.assertRaisesRegex(frappe.ValidationError, "belongs to company", bonus.insert)
