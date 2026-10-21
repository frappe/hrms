# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import nowdate

from hrms.payroll.doctype.employee_benefit_claim.test_employee_benefit_claim import (
	setup_employee_with_benefits,
)
from hrms.tests.utils import HRMSTestSuite


class TestEmployeeBenefitApplication(HRMSTestSuite):
	def test_limits_and_totals_are_set_server_side(self):
		employee, _, payroll_period = setup_employee_with_benefits("test_benefit_application@app.com")
		assignment = frappe.db.get_value(
			"Salary Structure Assignment", {"employee": employee, "docstatus": 1}, "name"
		)
		frappe.db.set_value("Salary Structure Assignment", assignment, "max_benefits", 86000)

		def make_application(rows, date=None):
			return frappe.get_doc(
				{
					"doctype": "Employee Benefit Application",
					"employee": employee,
					"company": "_Test Company",
					"date": date or nowdate(),
					"payroll_period": payroll_period.name,
					"currency": "INR",
					"max_benefits": 1000000,
					"employee_benefits": [
						{"salary_component": component, "max_benefit_amount": 1000000, "amount": amount}
						for component, amount in rows
					],
				}
			)

		self.assertRaises(frappe.ValidationError, make_application([("Basic Salary", 1000)]).insert)
		self.assertRaises(
			frappe.ValidationError, make_application([("Internet Reimbursement", 100000)]).insert
		)
		self.assertRaises(
			frappe.ValidationError,
			make_application([("Internet Reimbursement", 6000)], date="2050-01-01").insert,
		)

		application = make_application([("Internet Reimbursement", 6000)])
		application.insert()
		self.assertEqual(application.max_benefits, 86000)
		self.assertEqual(application.employee_benefits[0].max_benefit_amount, 12000)
		self.assertEqual(application.total_amount, 6000)
		self.assertEqual(application.remaining_benefit, 80000)
