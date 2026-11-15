import frappe
from frappe.tests import IntegrationTestCase

from hrms.patches.v16_0.add_rejection_reasons_and_scope_email_templates import execute
from hrms.patches.v16_0.replace_status_hiring_pipeline_board import execute as replace_status_board
from hrms.patches.v16_0.set_interview_applicant_name import execute as set_interview_applicant_name
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

	def test_status_hiring_pipeline_is_replaced_by_the_standard_board(self):
		frappe.flags.in_migrate = True
		self.addCleanup(setattr, frappe.flags, "in_migrate", False)
		frappe.delete_doc("Kanban Board", "Hiring Pipeline", force=True, ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Kanban Board",
				"kanban_board_name": "Hiring Pipeline",
				"reference_doctype": "Job Applicant",
				"field_name": "status",
			}
		).insert(ignore_permissions=True)

		replace_status_board()
		replace_status_board()
		board = frappe.db.get_value(
			"Kanban Board", "Hiring Pipeline", ["field_name", "is_standard"], as_dict=True
		)
		self.assertEqual((board.field_name, board.is_standard), ("stage", "Yes"))

	def test_interview_applicant_name_is_filled_once(self):
		applicant = frappe.get_doc(
			{
				"doctype": "Job Applicant",
				"applicant_name": "Named Later",
				"email_id": "named.later@example.com",
			}
		).insert()
		interview = frappe.get_doc(
			{"doctype": "Interview", "job_applicant": applicant.name, "scheduled_on": frappe.utils.nowdate()}
		)
		interview.flags.ignore_validate = True
		interview.insert(ignore_mandatory=True)
		interview.db_set("applicant_name", None)

		set_interview_applicant_name()
		set_interview_applicant_name()
		self.assertEqual(frappe.db.get_value("Interview", interview.name, "applicant_name"), "Named Later")
