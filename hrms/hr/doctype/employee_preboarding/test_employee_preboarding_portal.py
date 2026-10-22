# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import json

import frappe

from hrms.hr.doctype.employee_preboarding.employee_preboarding import PREBOARDING_CANDIDATE_ROLE
from hrms.hr.doctype.employee_preboarding.employee_preboarding_portal import (
	get_preboarding_form,
	save_preboarding_form,
	submit_preboarding_form,
)
from hrms.hr.doctype.employee_preboarding.test_employee_preboarding import (
	create_employee_preboarding,
	create_preboarding_employee,
)
from hrms.tests.utils import HRMSTestSuite

DETAILS = {
	"first_name": "Asha",
	"last_name": "Menon",
	"date_of_birth": "1998-04-12",
	"cell_number": "9876543210",
	"passport_number": "P1234567",
	"bank_name": "Test Bank",
	"education": [{"school_univ": "Test University", "qualification": "BSc"}],
	"external_work_history": [{"company_name": "Prior Co", "designation": "Analyst"}],
}


class TestEmployeePreboardingPortal(HRMSTestSuite):
	def setUp(self):
		frappe.set_user("Administrator")
		self.preboarding = create_employee_preboarding(submit=False)
		self.preboarding.db_set("personal_email", "portal.candidate@example.com")
		self.preboarding.db_set("create_user_for", "Personal Email")
		self.preboarding.reload()
		self.user = self.preboarding.create_user()
		self.details = {**DETAILS, "gender": frappe.db.get_value("Gender", {}, "name")}
		self.addCleanup(frappe.set_user, "Administrator")

	def test_create_user_grants_the_candidate_role(self):
		roles = {row.role for row in frappe.get_doc("User", self.user).roles}
		self.assertIn(PREBOARDING_CANDIDATE_ROLE, roles)

	def test_candidate_role_survives_a_user_save(self):
		"""erpnext strips Employee and Employee Self Service when no Employee is mapped."""
		user = frappe.get_doc("User", self.user)
		user.save(ignore_permissions=True)

		roles = {row.role for row in frappe.get_doc("User", self.user).roles}
		self.assertIn(PREBOARDING_CANDIDATE_ROLE, roles)

	def test_form_carries_the_requested_documents(self):
		self.preboarding.append("documents", {"document_name": "Aadhaar", "required": 1})
		self.preboarding.save()

		frappe.set_user(self.user)
		form = get_preboarding_form()

		self.assertTrue(form["allowed"])
		self.assertEqual([row["document_name"] for row in form["documents"]], ["Aadhaar"])

	def test_link_fields_are_sent_as_selects_with_options(self):
		frappe.set_user(self.user)
		form = get_preboarding_form()

		gender = next(f for s in form["sections"] for f in s["fields"] if f["fieldname"] == "gender")
		self.assertEqual(gender["fieldtype"], "Select")
		self.assertIn("", gender["options"])

	def test_a_user_without_the_role_is_refused(self):
		user = frappe.get_doc(
			{"doctype": "User", "email": "portal.norole@example.com", "first_name": "No Role"}
		).insert(ignore_permissions=True)
		self.addCleanup(frappe.delete_doc, "User", user.name, force=True, ignore_permissions=True)

		frappe.set_user(user.name)
		self.assertEqual(get_preboarding_form()["reason"], "no_role")

	def test_a_user_without_a_preboarding_cannot_save(self):
		user = frappe.get_doc(
			{"doctype": "User", "email": "portal.stranger@example.com", "first_name": "Stranger"}
		).insert(ignore_permissions=True)
		self.addCleanup(frappe.delete_doc, "User", user.name, force=True, ignore_permissions=True)

		frappe.set_user(user.name)
		with self.assertRaises(frappe.PermissionError):
			save_preboarding_form(json.dumps(self.details))

	def test_save_keeps_only_the_portal_fields(self):
		frappe.set_user(self.user)
		save_preboarding_form(
			json.dumps({**self.details, "boarding_status": "Completed", "company": "Hacked"})
		)

		self.preboarding.reload()
		blob = json.loads(self.preboarding.submitted_details)
		self.assertNotIn("boarding_status", blob)
		self.assertNotIn("company", blob)
		self.assertEqual(blob["first_name"], "Asha")
		self.assertNotEqual(self.preboarding.boarding_status, "Completed")

	def test_save_drops_empty_table_rows(self):
		frappe.set_user(self.user)
		save_preboarding_form(
			json.dumps({**self.details, "education": [{"school_univ": ""}, {"qualification": "BA"}]})
		)

		self.preboarding.reload()
		blob = json.loads(self.preboarding.submitted_details)
		self.assertEqual(blob["education"], [{"qualification": "BA"}])

	def test_uploaded_file_is_linked_to_its_row(self):
		self.preboarding.append("documents", {"document_name": "Aadhaar", "required": 1})
		self.preboarding.save()

		frappe.set_user(self.user)
		uploaded = frappe.get_doc(
			{"doctype": "File", "file_name": "aadhaar.txt", "is_private": 1, "content": "x"}
		).insert(ignore_permissions=True)
		save_preboarding_form(
			json.dumps(self.details), json.dumps([{"idx": 1, "attachment": uploaded.file_url}])
		)

		frappe.set_user("Administrator")
		self.preboarding.reload()
		self.assertEqual(self.preboarding.documents[0].attachment, uploaded.file_url)
		self.assertEqual(
			frappe.db.get_value("File", uploaded.name, "attached_to_name"), self.preboarding.name
		)

	def test_details_reach_the_new_employee(self):
		frappe.set_user(self.user)
		save_preboarding_form(json.dumps(self.details))

		frappe.set_user("Administrator")
		self.preboarding.reload()
		self.preboarding.submit()
		employee = frappe.get_doc("Employee", create_preboarding_employee(self.preboarding))

		self.assertEqual(employee.first_name, "Asha")
		self.assertEqual(str(employee.date_of_birth), "1998-04-12")
		self.assertEqual(employee.cell_number, "9876543210")
		self.assertEqual(employee.passport_number, "P1234567")
		self.assertEqual(len(employee.education), 1)
		self.assertEqual(len(employee.external_work_history), 1)
		self.assertEqual(employee.company, self.preboarding.company)

	def test_saving_is_blocked_once_the_employee_exists(self):
		frappe.set_user(self.user)
		save_preboarding_form(json.dumps(self.details))

		frappe.set_user("Administrator")
		self.preboarding.reload()
		self.preboarding.submit()
		create_preboarding_employee(self.preboarding)

		frappe.set_user(self.user)
		with self.assertRaises(frappe.ValidationError):
			save_preboarding_form(json.dumps(self.details))

	def test_hr_can_correct_the_submission(self):
		frappe.set_user(self.user)
		save_preboarding_form(json.dumps(self.details))

		frappe.set_user("Administrator")
		self.preboarding.reload()
		self.preboarding.update_submitted_details({**self.details, "first_name": "Corrected"})

		self.preboarding.reload()
		self.assertEqual(json.loads(self.preboarding.submitted_details)["first_name"], "Corrected")

	def test_submitting_locks_the_form(self):
		frappe.set_user(self.user)
		submit_preboarding_form(json.dumps(self.details))

		form = get_preboarding_form()
		self.assertTrue(form["is_submitted"])
		self.assertTrue(form["is_locked"])
		self.assertTrue(form["confirmed_on"])

	def test_a_submitted_form_cannot_be_saved_again(self):
		frappe.set_user(self.user)
		submit_preboarding_form(json.dumps(self.details))

		with self.assertRaises(frappe.ValidationError):
			save_preboarding_form(json.dumps({**self.details, "first_name": "Changed"}))

	def test_hr_can_still_correct_a_submitted_form(self):
		frappe.set_user(self.user)
		submit_preboarding_form(json.dumps(self.details))

		frappe.set_user("Administrator")
		self.preboarding.reload()
		self.preboarding.update_submitted_details({**self.details, "first_name": "Corrected"})

		self.preboarding.reload()
		self.assertEqual(json.loads(self.preboarding.submitted_details)["first_name"], "Corrected")

	def test_the_candidate_role_lands_on_the_portal(self):
		from hrms.hr.doctype.employee_preboarding.employee_preboarding import PORTAL_ROUTE

		home_page = frappe.db.get_value("Role", PREBOARDING_CANDIDATE_ROLE, "home_page")
		self.assertEqual(home_page, PORTAL_ROUTE.lstrip("/"))
