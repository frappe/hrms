# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


def create_position_template(template_name: str, template_code: str, **kwargs):
	if frappe.db.exists("Position Template", template_name):
		return frappe.get_doc("Position Template", template_name)

	return frappe.get_doc(
		{
			"doctype": "Position Template",
			"template_name": template_name,
			"template_code": template_code,
			**kwargs,
		}
	).insert(ignore_permissions=True)


class TestPositionTemplate(FrappeTestCase):
	def test_create(self):
		template = create_position_template("Test Teller", "TTEL")
		self.assertEqual(template.name, "Test Teller")

	def test_self_parent_blocked(self):
		template = create_position_template("Test Manager", "TMGR")
		template.parent_position_template = template.name
		self.assertRaises(frappe.ValidationError, template.save)
