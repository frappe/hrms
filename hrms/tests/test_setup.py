import frappe
from frappe.tests import IntegrationTestCase

from hrms.patches.v16_0.add_rejection_reasons_and_scope_email_templates import execute
from hrms.setup import HIRING_EMAIL_TEMPLATES, OFFER_EMAIL_TEMPLATES


class TestHiringDefaults(IntegrationTestCase):
	def setUp(self):
		self.addCleanup(frappe.db.rollback)

	def reference(self, template):
		return frappe.db.get_value("Email Template", template, "reference_doctype")

	def test_seed_patch_is_idempotent(self):
		frappe.db.delete("Email Template", {"name": "Offer follow-up"})
		execute()
		execute()
		self.assertEqual(frappe.db.count("Email Template", {"name": "Offer follow-up"}), 1)
		for template in HIRING_EMAIL_TEMPLATES:
			self.assertEqual(self.reference(template), "Job Applicant")

	def test_offer_templates_are_scoped_to_job_offer(self):
		execute()
		for template in OFFER_EMAIL_TEMPLATES:
			self.assertEqual(self.reference(template), "Job Offer")

	def test_patch_scopes_only_blank_templates(self):
		frappe.db.set_value("Email Template", "Interview Reminder", "reference_doctype", None)
		frappe.db.set_value("Email Template", "Leave Status Notification", "reference_doctype", "Employee")
		execute()
		self.assertEqual(self.reference("Interview Reminder"), "Interview")
		self.assertEqual(self.reference("Leave Status Notification"), "Employee")
