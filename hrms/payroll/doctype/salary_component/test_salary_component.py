# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe

from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure
from hrms.tests.utils import HRMSTestSuite


class TestSalaryComponent(HRMSTestSuite):
	def test_update_salary_structures(self):
		salary_component = create_salary_component("Special Allowance")
		salary_component.condition = "H < 10000"
		salary_component.formula = "BS*.5"
		salary_component.save()

		salary_structure1 = make_salary_structure("Salary Structure 1", "Monthly", company="_Test Company")
		salary_structure2 = make_salary_structure("Salary Structure 2", "Monthly", company="_Test Company")
		salary_structure3 = make_salary_structure("Salary Structure 3", "Monthly", company="_Test Company")
		salary_structure3.cancel()  # Details should not update for cancelled Salary Structures

		OLD_FORMULA = "BS\n*.5"
		OLD_CONDITION = "H < 10000"

		ss1_detail = next(
			(d for d in salary_structure1.earnings if d.salary_component == "Special Allowance"), None
		)
		self.assertEqual(ss1_detail.condition, OLD_CONDITION)
		self.assertEqual(ss1_detail.formula, OLD_FORMULA)

		ss2_detail = next(
			(d for d in salary_structure2.earnings if d.salary_component == "Special Allowance"), None
		)
		self.assertEqual(ss2_detail.condition, OLD_CONDITION)
		self.assertEqual(ss2_detail.formula, OLD_FORMULA)

		ss3_detail = next(
			(d for d in salary_structure3.earnings if d.salary_component == "Special Allowance"), None
		)
		self.assertEqual(ss3_detail.condition, OLD_CONDITION)
		self.assertEqual(ss3_detail.formula, OLD_FORMULA)

		salary_component.db_set("condition", "H < 8000")
		salary_component.update_salary_structures("condition")
		ss1_detail.reload()
		self.assertEqual(ss1_detail.condition, "H < 8000")
		ss2_detail.reload()
		self.assertEqual(ss2_detail.condition, "H < 8000")
		ss3_detail.reload()
		self.assertEqual(ss3_detail.condition, OLD_CONDITION)
		salary_component.db_set({"amount_based_on_formula": 1, "formula": "BS*.3"})
		salary_component.update_salary_structures("formula")
		ss1_detail.reload()
		self.assertEqual(ss1_detail.formula, "BS*.3")
		ss2_detail.reload()
		self.assertEqual(ss2_detail.formula, "BS*.3")
		ss3_detail.reload()
		self.assertEqual(ss3_detail.formula, OLD_FORMULA)

	def test_update_salary_structures_uses_saved_values(self):
		salary_structure = make_salary_structure("Salary Structure 1", "Monthly", company="_Test Company")
		detail = next(d for d in salary_structure.earnings if d.salary_component == "Special Allowance")

		salary_component = frappe.get_doc("Salary Component", "Special Allowance")
		salary_component.db_set({"amount_based_on_formula": 1, "formula": "BS*.5"})

		self.assertRaises(frappe.ValidationError, salary_component.update_salary_structures, "amount")

		salary_component.formula = "BS*5"
		salary_component.update_salary_structures("formula")
		detail.reload()
		self.assertEqual(detail.formula, "BS*.5")

		salary_component.db_set({"amount_based_on_formula": 0, "formula": "", "amount": 1500})
		salary_component.update_salary_structures("formula")
		detail.reload()
		self.assertEqual(detail.amount_based_on_formula, 0)
		self.assertEqual(detail.formula, None)
		self.assertEqual(detail.amount, 1500)


def create_salary_component(component_name, **args):
	if frappe.db.exists("Salary Component", component_name):
		return frappe.get_doc("Salary Component", component_name)

	return frappe.get_doc(
		{
			"doctype": "Salary Component",
			"salary_component": component_name,
			"type": args.get("type") or "Earning",
			"is_tax_applicable": args.get("is_tax_applicable") or 1,
			"do_not_include_in_total": args.get("do_not_include_in_total") or 0,
			"do_not_include_in_accounts": args.get("do_not_include_in_accounts") or 0,
		}
	).insert()
