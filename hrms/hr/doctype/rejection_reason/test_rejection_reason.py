import frappe
from frappe.tests import IntegrationTestCase

from hrms.hr.doctype.rejection_reason.rejection_reason import DEFAULT_REASONS, create_default_reasons


class TestRejectionReason(IntegrationTestCase):
	def setUp(self):
		self.addCleanup(frappe.db.rollback)

	def test_default_reasons_are_added_once(self):
		frappe.db.delete("Rejection Reason", {"name": "Withdrew"})
		create_default_reasons()
		create_default_reasons()
		for reason in DEFAULT_REASONS:
			self.assertEqual(frappe.db.count("Rejection Reason", {"name": reason}), 1)
