# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestOrganizationUnit(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_level_calculation(self):
		root = create_organization_unit("_Test Exec Office", is_group=1)
		child = create_organization_unit("_Test Tech Office", parent=root.name, is_group=1)
		grandchild = create_organization_unit("_Test Dev Dept", parent=child.name)

		self.assertEqual(root.organization_level, 1)
		self.assertEqual(child.organization_level, 2)
		self.assertEqual(grandchild.organization_level, 3)

	def test_circular_reference(self):
		root = create_organization_unit("_Test Circular Root", is_group=1)
		child = create_organization_unit("_Test Circular Child", parent=root.name, is_group=1)

		root.parent_organization_unit = child.name
		self.assertRaises(frappe.ValidationError, root.save)

	def test_level_recalculation_on_move(self):
		root_a = create_organization_unit("_Test Root A", is_group=1)
		root_b = create_organization_unit("_Test Root B", is_group=1)
		movable = create_organization_unit("_Test Movable", parent=root_a.name, is_group=1)
		leaf = create_organization_unit("_Test Leaf", parent=movable.name)

		movable.parent_organization_unit = root_b.name
		movable.save()

		leaf.reload()
		self.assertEqual(leaf.organization_level, 3)


def create_organization_unit(unit_name: str, parent: str = None, is_group: int = 0, **kwargs):
	if frappe.db.exists("Organization Unit", unit_name):
		return frappe.get_doc("Organization Unit", unit_name)

	return frappe.get_doc(
		{
			"doctype": "Organization Unit",
			"unit_name": unit_name,
			"parent_organization_unit": parent,
			"is_group": is_group,
			**kwargs,
		}
	).insert()
