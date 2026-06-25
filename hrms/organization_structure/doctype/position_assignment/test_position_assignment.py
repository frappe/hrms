# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.organization_structure.doctype.position.test_position import create_position


class TestPositionAssignment(FrappeTestCase):
	def setUp(self):
		self.position = create_position("_Test Assignable CEO")
		self.employee1 = make_employee("orgstruct1@example.com", company="_Test Company")
		self.employee2 = make_employee("orgstruct2@example.com", company="_Test Company")

	def tearDown(self):
		frappe.db.rollback()

	def test_position_marked_occupied(self):
		self._create_assignment(self.employee1)

		self.position.reload()
		self.assertTrue(self.position.is_occupied)
		self.assertEqual(self.position.current_employee, self.employee1)

	def test_single_active_assignment(self):
		self._create_assignment(self.employee1)
		second = frappe.get_doc(
			{
				"doctype": "Position Assignment",
				"employee": self.employee2,
				"position": self.position.name,
				"start_date": "2026-01-01",
				"status": "Active",
			}
		)
		self.assertRaises(frappe.ValidationError, second.insert)

	def test_position_becomes_vacant(self):
		assignment = self._create_assignment(self.employee1)
		assignment.status = "Inactive"
		assignment.save()

		self.position.reload()
		self.assertFalse(self.position.is_occupied)

	def _create_assignment(self, employee):
		return frappe.get_doc(
			{
				"doctype": "Position Assignment",
				"employee": employee,
				"position": self.position.name,
				"start_date": "2026-01-01",
				"status": "Active",
			}
		).insert()
