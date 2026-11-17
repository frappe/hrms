# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_months, nowdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure


class TestSalaryStructureAssignment(FrappeTestCase):
	def test_employee_currency_ignores_draft_and_cancelled_assignments(self):
		from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import (
			get_employee_currency,
		)

		emp = make_employee("ssa_employee_currency@test.com", company="_Test Company")
		make_salary_structure(
			"SSA Test Currency INR",
			"Monthly",
			employee=emp,
			company="_Test Company",
			currency="INR",
			from_date=add_months(nowdate(), -2),
		)
		usd_structure = make_salary_structure(
			"SSA Test Currency USD", "Monthly", company="_Test Company", currency="USD"
		)

		inr_assignment = frappe.get_last_doc("Salary Structure Assignment", filters={"employee": emp})
		usd_assignment = frappe.copy_doc(inr_assignment)
		usd_assignment.update(
			{
				"salary_structure": usd_structure.name,
				"docstatus": 0,
				"currency": "USD",
				"income_tax_slab": None,
				"from_date": add_months(nowdate(), -1),
			}
		)
		usd_assignment.insert()
		self.assertEqual(get_employee_currency(emp), "INR")

		usd_assignment.submit()
		self.assertEqual(get_employee_currency(emp), "USD")

		usd_assignment.cancel()
		self.assertEqual(get_employee_currency(emp), "INR")
