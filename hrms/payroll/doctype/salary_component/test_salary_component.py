# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure


class TestSalaryComponent(IntegrationTestCase):
	def test_update_salary_structures(self):
		salary_component = create_salary_component("Special Allowance")
		salary_component.condition = "H < 10000"
		salary_component.formula = "BS*.5"
		salary_component.save()

		salary_structure1 = make_salary_structure("Salary Structure 1", "Monthly")
		salary_structure2 = make_salary_structure("Salary Structure 2", "Monthly")
		salary_structure3 = make_salary_structure("Salary Structure 3", "Monthly")
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

		salary_component.update_salary_structures("condition", "H < 8000")
		ss1_detail.reload()
		self.assertEqual(ss1_detail.condition, "H < 8000")
		ss2_detail.reload()
		self.assertEqual(ss2_detail.condition, "H < 8000")
		ss3_detail.reload()
		self.assertEqual(ss3_detail.condition, OLD_CONDITION)

		salary_component.update_salary_structures("formula", "BS*.3")
		ss1_detail.reload()
		self.assertEqual(ss1_detail.formula, "BS*.3")
		ss2_detail.reload()
		self.assertEqual(ss2_detail.formula, "BS*.3")
		ss3_detail.reload()
		self.assertEqual(ss3_detail.formula, OLD_FORMULA)


def create_salary_component(component_name, **args):
	if frappe.db.exists("Salary Component", component_name):
		return frappe.get_doc("Salary Component", component_name)

	return frappe.get_doc(
		{
			"doctype": "Salary Component",
			"salary_component": component_name,
			"type": args.get("type") or "Earning",
			"is_tax_applicable": args.get("is_tax_applicable") or 1,
		}
	).insert()
