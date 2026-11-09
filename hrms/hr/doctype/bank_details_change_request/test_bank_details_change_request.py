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
		request.submit()

		self.assertIsNone(frappe.db.get_value("Employee", self.employee, "bank_ac_no"))

	def test_open_request_cannot_be_submitted(self):
		request = self.make_request()
		self.assertRaises(frappe.ValidationError, request.submit)

	def test_one_open_request_per_employee(self):
		self.make_request()
		self.assertRaises(frappe.ValidationError, self.make_request, bank_ac_no="99887766")

	def test_cancelled_request_is_closed(self):
		request = self.make_request()
		request.status = "Cancelled"
		request.save()

		# it no longer stops a new request, and is not taken up again
		self.make_request(bank_ac_no="99887766")
		self.assertRaises(frappe.ValidationError, request.submit)
		request.reload()
		request.status = "Open"
		self.assertRaises(frappe.ValidationError, request.save)

	def test_employee_cannot_approve_their_own_request(self):
		frappe.set_user(USER)
		request = self.make_request()
		request.status = "Approved"
		self.assertRaises(frappe.PermissionError, request.save)
