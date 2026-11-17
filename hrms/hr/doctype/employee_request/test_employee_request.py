# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import os
from email import message_from_string

import frappe
from frappe.tests.classes.context_managers import set_user
from frappe.utils import add_days, getdate
from frappe.utils.file_manager import save_file

from hrms.hr.doctype.employee_onboarding.employee_onboarding import make_employee
from hrms.hr.doctype.employee_onboarding.test_employee_onboarding import (
	create_employee_onboarding,
	get_test_template,
	get_test_user,
)
from hrms.hr.doctype.employee_request.employee_request import (
	PREBOARDING_CANDIDATE_ROLE,
	PREBOARDING_INVITE_MESSAGE,
	PREBOARDING_INVITE_TEMPLATE,
	get_permission_query_conditions,
	has_permission,
)
from hrms.tests.utils import HRMSTestSuite

CANDIDATE_EMAIL = "asha.candidate@example.com"


class TestEmployeeRequest(HRMSTestSuite):
	def test_create_user_login_starts_the_request(self):
		onboarding = start_onboarding()
		request = get_request(onboarding)

		self.assertIn(PREBOARDING_CANDIDATE_ROLE, frappe.get_roles(CANDIDATE_EMAIL))
		self.assertEqual(request.user, CANDIDATE_EMAIL)
		self.assertEqual(request.first_name, "Test")
		self.assertEqual(
			[(row.document_name, row.required) for row in request.documents],
			[("PAN Card", 1), ("Degree Certificate", 0)],
		)

	def test_a_new_user_gets_one_email_with_the_password_and_preboarding_links(self):
		email = "asha.new.candidate@example.com"
		frappe.delete_doc("User", email, force=True, ignore_missing=True)
		frappe.db.delete("Email Queue")

		start_onboarding(email=email)

		messages = get_sent_messages(email)
		self.assertEqual(len(messages), 1)
		self.assertIn("/update-password?key=", messages[0])
		self.assertIn("/preboarding", messages[0])

	def test_an_existing_user_is_invited_without_a_password_link(self):
		get_test_user(CANDIDATE_EMAIL)
		frappe.db.delete("Email Queue")

		start_onboarding()

		messages = get_sent_messages(CANDIDATE_EMAIL)
		self.assertEqual(len(messages), 1)
		self.assertNotIn("/update-password", messages[0])
		self.assertIn("/preboarding", messages[0])

	def test_the_new_hire_sees_only_their_own_request(self):
		request = get_request(start_onboarding())

		self.assertIn(frappe.db.escape(CANDIDATE_EMAIL), get_permission_query_conditions(CANDIDATE_EMAIL))
		self.assertFalse(has_permission(frappe._dict(user="someone.else@example.com"), user=CANDIDATE_EMAIL))
		self.assertTrue(has_permission(request, user=CANDIDATE_EMAIL))

		with self.set_user(CANDIDATE_EMAIL):
			request.employee_onboarding = "HR-EMP-ONB-NOT-MINE"
			request.save()
			request.reload()
			self.assertNotEqual(request.employee_onboarding, "HR-EMP-ONB-NOT-MINE")

			request.documents = request.documents[:1]
			self.assertRaises(frappe.PermissionError, request.save)

	def test_details_are_checked_only_on_submit(self):
		request = get_request(start_onboarding())
		with self.set_user(CANDIDATE_EMAIL):
			request.cell_number = "+91-9876543210"
			request.documents[0].attachment = upload_file("pan.txt").file_url
			request.save()
			self.assertRaises(frappe.MandatoryError, request.submit_details)

			request.reload()
			fill_mandatory_details(request)
			request.save()
			request.submit_details()
			request.reload()

		self.assertTrue(request.submitted_on)
		self.assertTrue(request.documents[0].attachment.startswith("/private/"))

	def test_onboarding_awaits_details_until_the_request_is_submitted(self):
		onboarding = start_onboarding()
		self.assertEqual(get_boarding_status(onboarding), "Awaiting Employee Details")

		request = get_request(onboarding)
		with self.set_user(CANDIDATE_EMAIL):
			fill_mandatory_details(request)
			request.cell_number = "+91-9876543210"
			request.documents[0].attachment = upload_file("pan.txt").file_url
			request.save()
			request.submit_details()

		self.assertEqual(get_boarding_status(onboarding), "Details Submitted")

	def test_required_documents_block_submit(self):
		request = get_request(start_onboarding())
		with self.set_user(CANDIDATE_EMAIL):
			fill_mandatory_details(request)
			request.save()

			self.assertRaises(frappe.ValidationError, request.submit_details)

	def test_create_employee_dialog_gets_the_request(self):
		onboarding = start_onboarding()
		request = get_request(onboarding)
		fill_mandatory_details(request)
		request.bank_name = "HDFC Bank"
		request.save()

		employee = make_employee(onboarding.name)
		details = employee.get_onload().employee_details

		self.assertEqual((employee.gender, employee.bank_name), ("Female", "HDFC Bank"))
		self.assertEqual(details["name"], request.name)
		self.assertIn("bank_name", details["fields"])
		self.assertEqual(
			[(document["label"], document["url"]) for document in details["documents"]],
			[(row.document_name, None) for row in request.documents],
		)

	def test_employee_from_the_list_fills_only_blank_fields_and_retires_the_request(self):
		onboarding = start_onboarding()
		request = get_request(onboarding)
		fill_mandatory_details(request)
		request.update({"bank_name": "HDFC Bank", "cell_number": "+91-9876543210"})
		request.documents[0].attachment = upload_file("old_pan.txt").file_url
		request.save()
		request.documents[0].attachment = upload_file("pan.txt").file_url
		request.save()

		employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "Asha",
				"gender": "Female",
				"date_of_birth": "1995-02-01",
				"date_of_joining": getdate(),
				"company": onboarding.company,
				"job_offer": onboarding.job_offer,
				"bank_name": "State Bank of India",
			}
		).insert()
		employee.reload()

		self.assertEqual(employee.bank_name, "State Bank of India")
		self.assertEqual(employee.cell_number, "+91-9876543210")
		self.assertEqual(employee.documents, [])
		self.assertFalse(frappe.db.exists("Employee Request", request.name))
		self.assertNotIn(PREBOARDING_CANDIDATE_ROLE, frappe.get_roles(CANDIDATE_EMAIL))
		self.assertEqual(
			frappe.get_all(
				"File",
				filters={"attached_to_doctype": "Employee", "attached_to_name": employee.name},
				pluck="file_name",
			),
			["PAN Card.txt"],
		)

	def test_hr_manager_starts_and_retires_the_request(self):
		hr_manager = get_test_user("asha.hr.manager@example.com")
		frappe.get_doc("User", hr_manager).add_roles("HR Manager")
		onboarding = start_onboarding(as_user=hr_manager)
		request = get_request(onboarding)
		self.assertIn(PREBOARDING_CANDIDATE_ROLE, frappe.get_roles(CANDIDATE_EMAIL))

		fill_mandatory_details(request)
		request.save()
		with self.set_user(hr_manager):
			make_employee(onboarding.name).insert()

		self.assertFalse(frappe.db.exists("Employee Request", request.name))
		self.assertNotIn(PREBOARDING_CANDIDATE_ROLE, frappe.get_roles(CANDIDATE_EMAIL))

	def test_saving_makes_only_the_requests_own_files_private(self):
		onboarding = start_onboarding()
		request = get_request(onboarding)
		elsewhere = save_file("logo.txt", b"company logo", onboarding.doctype, onboarding.name, is_private=0)
		unattached = save_file("banner.txt", b"company banner", None, None, is_private=0)

		with self.set_user(CANDIDATE_EMAIL):
			for file in (elsewhere, unattached):
				request.reload()
				request.documents[0].attachment = file.file_url
				self.assertRaises(frappe.ValidationError, request.save)
				file.reload()
				self.assertFalse(file.is_private)
				self.assertTrue(os.path.exists(file.get_full_path()))

			request.reload()
			request.documents[0].attachment = save_file(
				"pan.txt", b"pan card", None, None, is_private=0
			).file_url
			request.save()

		self.assertTrue(request.documents[0].attachment.startswith("/private/"))
		self.assertTrue(
			frappe.db.exists(
				"File",
				{
					"file_url": request.documents[0].attachment,
					"attached_to_doctype": request.doctype,
					"attached_to_name": request.name,
				},
			)
		)

	def test_saving_accepts_only_the_requests_own_private_files(self):
		onboarding = start_onboarding()
		request = get_request(onboarding)
		elsewhere = save_file("offer.txt", b"offer letter", onboarding.doctype, onboarding.name, is_private=1)
		someone_elses = save_file("salary.txt", b"salary slip", None, None, is_private=1)

		with self.set_user(CANDIDATE_EMAIL):
			for file in (elsewhere, someone_elses):
				request.reload()
				request.documents[0].attachment = file.file_url
				self.assertRaises(frappe.ValidationError, request.save)
				self.assertFalse(
					frappe.db.exists(
						"File",
						{
							"file_url": file.file_url,
							"attached_to_doctype": request.doctype,
							"attached_to_name": request.name,
						},
					)
				)

			request.reload()
			request.documents[0].attachment = upload_file("pan.txt").file_url
			request.save()

		self.assertTrue(
			frappe.db.exists(
				"File",
				{
					"file_url": request.documents[0].attachment,
					"attached_to_doctype": request.doctype,
					"attached_to_name": request.name,
				},
			)
		)

	def test_saving_rejects_attachment_links_without_an_uploaded_file(self):
		onboarding = start_onboarding()
		request = get_request(onboarding)

		with self.set_user(CANDIDATE_EMAIL):
			for url in ("/private/files/does-not-exist/x.pdf", "https://example.com/x.pdf"):
				request.reload()
				request.documents[0].attachment = url
				self.assertRaises(frappe.ValidationError, request.save)
				self.assertFalse(frappe.db.exists("File", {"file_url": url}))


def start_onboarding(as_user=None, email=CANDIDATE_EMAIL):
	frappe.db.set_value(
		"Email Template", PREBOARDING_INVITE_TEMPLATE, "response_html", PREBOARDING_INVITE_MESSAGE
	)
	template = get_test_template()
	template.set(
		"required_documents",
		[
			{"document_name": "PAN Card", "required": 1},
			{"document_name": "Degree Certificate", "required": 0},
		],
	)
	template.save()

	onboarding = create_employee_onboarding(submit=True)
	onboarding.date_of_joining = add_days(getdate(), 7)
	with set_user(as_user or frappe.session.user):
		onboarding.create_user("Personal Email", personal_email=email)
	onboarding.reload()
	return onboarding


def get_boarding_status(onboarding):
	return frappe.db.get_value("Employee Onboarding", onboarding.name, "boarding_status")


def get_sent_messages(recipient):
	EmailQueue = frappe.qb.DocType("Email Queue")
	Recipient = frappe.qb.DocType("Email Queue Recipient")
	raw_messages = (
		frappe.qb.from_(EmailQueue)
		.join(Recipient)
		.on(Recipient.parent == EmailQueue.name)
		.select(EmailQueue.message)
		.where(Recipient.recipient == recipient)
		.run(pluck=True)
	)
	return [get_html_body(raw) for raw in raw_messages]


def get_html_body(raw):
	part = next(part for part in message_from_string(raw).walk() if part.get_content_type() == "text/html")
	return part.get_payload(decode=True).decode()


def get_request(onboarding):
	return frappe.get_doc("Employee Request", {"employee_onboarding": onboarding.name})


def fill_mandatory_details(request):
	request.update({"first_name": "Asha", "gender": "Female", "date_of_birth": "1995-02-01"})


def upload_file(file_name):
	return save_file(file_name, b"test document", None, None, is_private=1)
