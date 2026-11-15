import frappe
from frappe.tests import IntegrationTestCase

from hrms.patches.v16_0.show_employee_name_in_links import execute
from hrms.setup import EMPLOYEE_NAME_IN_LINKS


class TestEmployeeNameInLinks(IntegrationTestCase):
	def setUp(self):
		self.addCleanup(frappe.db.rollback)
		frappe.db.delete("Property Setter", EMPLOYEE_NAME_IN_LINKS)

	def get_values(self):
		return frappe.get_all("Property Setter", filters=EMPLOYEE_NAME_IN_LINKS, pluck="value")

	def test_patch_shows_the_name_once(self):
		execute()
		execute()
		self.assertEqual(self.get_values(), ["1"])

	def test_patch_keeps_a_site_choice(self):
		frappe.make_property_setter(
			{
				"doctype": "Employee",
				"doctype_or_field": "DocType",
				"property": "show_title_field_in_link",
				"value": 0,
				"property_type": "Check",
			}
		)
		execute()
		self.assertEqual(self.get_values(), ["0"])
