# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from hrms.organization_structure.doctype.position_template.test_position_template import (
	create_position_template,
)


def create_branch_staffing_template(template_name: str, rows: list[tuple[str, int]], **kwargs):
	if frappe.db.exists("Branch Staffing Template", template_name):
		return frappe.get_doc("Branch Staffing Template", template_name)

	doc = frappe.get_doc(
		{
			"doctype": "Branch Staffing Template",
			"template_name": template_name,
			"staffing_details": [
				{"position_template": template, "quantity": qty} for template, qty in rows
			],
			**kwargs,
		}
	)
	return doc.insert(ignore_permissions=True)


class TestBranchStaffingTemplate(FrappeTestCase):
	def test_create(self):
		create_position_template("Test BST Teller", "TBTEL")
		template = create_branch_staffing_template("Test Small Branch", [("Test BST Teller", 3)])
		self.assertEqual(template.total_positions(), 3)

	def test_duplicate_template_blocked(self):
		create_position_template("Test BST Guard", "TBGRD")
		doc = frappe.get_doc(
			{
				"doctype": "Branch Staffing Template",
				"template_name": "Test Dup Branch",
				"staffing_details": [
					{"position_template": "Test BST Guard", "quantity": 1},
					{"position_template": "Test BST Guard", "quantity": 2},
				],
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert)
