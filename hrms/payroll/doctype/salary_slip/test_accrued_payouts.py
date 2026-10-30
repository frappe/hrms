# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from unittest.mock import patch

import frappe

from hrms.tests.utils import HRMSTestSuite


class TestAccruedPayouts(HRMSTestSuite):
	def test_payouts_are_not_prorated_again_in_totals(self):
		for payment_days in (15, 0):
			for reference in ("Arrear", "Payroll Correction", "Employee Benefit Claim", None):
				with self.subTest(payment_days=payment_days, reference=reference):
					slip = frappe.get_doc(
						{
							"doctype": "Salary Slip",
							"salary_structure": "Test Structure",
							"total_working_days": 30,
							"payment_days": payment_days,
						}
					)
					component = frappe._dict(
						salary_component="Basic",
						abbr="B",
						depends_on_payment_days=1,
						accrual_component=not reference,
					)
					additional_salary = (
						frappe._dict(name="TEST-ADDITIONAL", ref_doctype=reference) if reference else None
					)
					get_value = frappe.db.get_value

					def lookup(doctype, *args, **kwargs):
						if doctype == "Additional Salary":
							return reference
						return get_value(doctype, *args, **kwargs)

					with patch.object(frappe.db, "get_value", side_effect=lookup):
						slip.update_component_row(component, 1000, "earnings", additional_salary)
						self.assertEqual(slip.earnings[0].amount, 1000)
						self.assertEqual(
							slip.get_component_totals("earnings", depends_on_payment_days=1), 1000
						)

	def test_ordinary_component_is_still_prorated(self):
		slip = frappe.get_doc(
			{
				"doctype": "Salary Slip",
				"salary_structure": "Test Structure",
				"total_working_days": 30,
				"payment_days": 15,
			}
		)
		component = frappe._dict(salary_component="Basic", abbr="B", depends_on_payment_days=1)
		slip.update_component_row(component, 1000, "earnings")
		self.assertEqual(slip.get_component_totals("earnings", depends_on_payment_days=1), 500)
