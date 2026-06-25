# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from hrms.organization_structure.doctype.organization_unit.test_organization_unit import (
	create_organization_unit,
)


class TestPosition(FrappeTestCase):
	def setUp(self):
		self.org_unit = create_organization_unit("_Test Position Office", is_group=1)

	def tearDown(self):
		frappe.db.rollback()

	def test_single_root_position(self):
		create_position("_Test CEO")

		second_root = frappe.get_doc(
			{
				"doctype": "Position",
				"position_name": "_Test Rogue Root",
				"organization_unit": self.org_unit.name,
			}
		)
		self.assertRaises(frappe.ValidationError, second_root.insert)

	def test_position_level(self):
		ceo = create_position("_Test CEO Level")
		cto = create_position("_Test CTO Level", parent=ceo.name)
		manager = create_position("_Test Mgr Level", parent=cto.name)

		self.assertEqual(ceo.position_level, 1)
		self.assertEqual(cto.position_level, 2)
		self.assertEqual(manager.position_level, 3)

	def test_circular_reference(self):
		ceo = create_position("_Test CEO Circular")
		cto = create_position("_Test CTO Circular", parent=ceo.name)

		ceo.parent_position = cto.name
		self.assertRaises(frappe.ValidationError, ceo.save)


def create_position(position_name: str, parent: str = None, org_unit: str = None, **kwargs):
	if frappe.db.exists("Position", position_name):
		return frappe.get_doc("Position", position_name)

	if not org_unit:
		org_unit = create_organization_unit("_Test Position Office", is_group=1).name

	return frappe.get_doc(
		{
			"doctype": "Position",
			"position_name": position_name,
			"organization_unit": org_unit,
			"parent_position": parent,
			**kwargs,
		}
	).insert()
