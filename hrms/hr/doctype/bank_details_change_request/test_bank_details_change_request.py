# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.tests.utils import HRMSTestSuite

USER = "bank_change@example.com"


class TestBankDetailsChangeRequest(HRMSTestSuite):
	def setUp(self):
		self.employee = make_employee(USER, company="_Test Company")
		self.addCleanup(frappe.set_user, "Administrator")

	def make_request(self, **kwargs):
		return frappe.get_doc(
			{
				"doctype": "Bank Details Change Request",
				"employee": self.employee,
				"bank_name": "Test Bank",
				"bank_ac_no": "001122334455",
				"iban": "GB33BUKB20201555555555",
				"proof": "/private/files/cheque.png",
				**kwargs,
			}
		).insert()

	def test_hr_hears_only_of_requests_they_may_see(self):
		# HR A and HR B split the employees between them by user permissions
		hr_a = make_hr_user("bank_change_hr_a@example.com")
		hr_b = make_hr_user("bank_change_hr_b@example.com")
		elsewhere = make_employee("bank_change_elsewhere@example.com", company="_Test Company")
		frappe.permissions.add_user_permission("Employee", elsewhere, hr_b)

		request = self.make_request()
		notified = frappe.get_all(
			"Notification Log",
			filters={"document_type": request.doctype, "document_name": request.name},
			fields=["for_user", "subject"],
		)
		subjects = {log.for_user: log.subject for log in notified}
		self.assertEqual(subjects.get(hr_a), f"{request.employee_name} asked to change their salary account")
		self.assertNotIn(hr_b, subjects)

	def test_approval_updates_the_employee(self):
		request = self.make_request()
		request.status = "Approved"
		request.submit()

		employee = frappe.db.get_value(
			"Employee", self.employee, ["salary_mode", "bank_name", "bank_ac_no", "iban"], as_dict=True
		)
		self.assertEqual(employee.salary_mode, "Bank")
		self.assertEqual(employee.bank_name, "Test Bank")
		self.assertEqual(employee.bank_ac_no, "001122334455")
		self.assertEqual(employee.iban, "GB33BUKB20201555555555")

	def test_rejection_leaves_the_employee(self):
		request = self.make_request()
		request.status = "Rejected"
		# a rejection says why
		self.assertRaises(frappe.ValidationError, request.submit)
		request.reload()
		request.status = "Rejected"
		request.rejection_reason = "The cheque is not readable"
		request.submit()

		self.assertIsNone(frappe.db.get_value("Employee", self.employee, "bank_ac_no"))

	def test_open_request_cannot_be_submitted(self):
		request = self.make_request()
		self.assertRaises(frappe.ValidationError, request.submit)

	def test_one_open_request_per_employee(self):
		self.make_request()
		self.assertRaises(frappe.ValidationError, self.make_request, bank_ac_no="99887766")

	def test_discarded_request_is_closed(self):
		request = self.make_request()
		# a draft is cancelled by discarding it, not by its status
		request.status = "Cancelled"
		self.assertRaises(frappe.ValidationError, request.save)

		request.reload()
		request.discard()
		request.reload()
		self.assertEqual((request.docstatus, request.status), (2, "Cancelled"))
		# it no longer stops a new request
		self.make_request(bank_ac_no="99887766")

	def test_employee_cannot_approve_their_own_request(self):
		frappe.set_user(USER)
		request = self.make_request()
		request.status = "Approved"
		self.assertRaises(frappe.PermissionError, request.save)


def make_hr_user(email: str) -> str:
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0}
		).insert()
	frappe.get_doc("User", email).add_roles("HR User")
	return email
