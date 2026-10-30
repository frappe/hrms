# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe

from hrms.tests.utils import HRMSTestSuite


class TestComponentConditions(HRMSTestSuite):
	def test_false_condition_removes_old_component_and_formula_values(self):
		for component_type in ("earnings", "deductions", "employer_contributions"):
			for additional_amount in (0, 100):
				with self.subTest(component_type=component_type, additional_amount=additional_amount):
					slip = frappe.get_doc({"doctype": "Salary Slip", "payment_days": 0})
					slip.append(
						component_type,
						{"salary_component": "Basic", "abbr": "B", "amount": 1000, "default_amount": 1000},
					)
					if additional_amount:
						slip.append(
							component_type,
							{
								"salary_component": "Basic",
								"abbr": "B",
								"amount": additional_amount,
								"additional_salary": "TEST-ADDITIONAL",
							},
						)
					slip.data = {"B": 1000, "payment_days": 0}
					slip.default_data = slip.data.copy()
					component = frappe._dict(
						salary_component="Basic", abbr="B", amount=1000, condition="payment_days > 0"
					)
					slip.add_structure_component(component, component_type)
					self.assertEqual(len(slip.get(component_type)), bool(additional_amount))
					self.assertEqual(slip.data["B"], additional_amount)
					self.assertEqual(slip.default_data["B"], 0)
					dependent = frappe._dict(
						abbr="D", amount_based_on_formula=1, formula="B / 2", precision=2
					)
					self.assertEqual(
						slip.eval_condition_and_formula(dependent, slip.data), additional_amount / 2
					)
					self.assertEqual(slip.eval_condition_and_formula(dependent, slip.default_data), 0)

	def test_false_statistical_condition_clears_formula_values(self):
		slip = frappe.get_doc({"doctype": "Salary Slip"})
		slip.data, slip.default_data = {"S": 1000}, {"S": 1000}
		component = frappe._dict(
			salary_component="Statistical", abbr="S", amount=1000, condition="False", statistical_component=1
		)
		slip.add_structure_component(component, "earnings")
		self.assertEqual(slip.data["S"], 0)
		self.assertEqual(slip.default_data["S"], 0)
