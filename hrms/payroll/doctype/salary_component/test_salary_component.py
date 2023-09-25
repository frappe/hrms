# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestSalaryComponent(FrappeTestCase):
	pass


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
