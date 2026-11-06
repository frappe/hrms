# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, getdate
from frappe.utils.file_manager import save_file

from hrms.hr.doctype.employee_preboarding.employee_preboarding import make_employee
from hrms.hr.doctype.employee_preboarding.test_employee_preboarding import (
	create_employee_preboarding,
	get_test_template,
	get_test_user,
)
from hrms.hr.doctype.employee_request.employee_request import (
	PREBOARDING_CANDIDATE_ROLE,
	get_permission_query_conditions,
	has_permission,
)
from hrms.tests.utils import HRMSTestSuite

CANDIDATE_EMAIL = "asha.candidate@example.com"


class TestEmployeeRequest(HRMSTestSuite):
	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_create_user_login_starts_the_request(self):
		preboarding = start_preboarding()
		request = get_request(preboarding)

		self.assertIn(PREBOARDING_CANDIDATE_ROLE, frappe.get_roles(CANDIDATE_EMAIL))
		self.assertEqual(request.user, CANDIDATE_EMAIL)
		self.assertEqual(request.first_name, "Test")
		self.assertEqual(
			[(row.document_name, row.required) for row in request.documents],
			[("PAN Card", 1), ("Degree Certificate", 0)],
		)
		self.assertTrue(
			frappe.db.exists(
				"Email Queue",
				{"reference_doctype": "Employee Preboarding", "reference_name": preboarding.name},
			)
		)

	def test_the_new_hire_sees_only_their_own_request(self):
		request = get_request(start_preboarding())

		self.assertIn(frappe.db.escape(CANDIDATE_EMAIL), get_permission_query_conditions(CANDIDATE_EMAIL))
		self.assertFalse(has_permission(frappe._dict(user="someone.else@example.com"), user=CANDIDATE_EMAIL))
		self.assertTrue(has_permission(request, user=CANDIDATE_EMAIL))

		frappe.set_user(CANDIDATE_EMAIL)
		request.employee_preboarding = "HR-EMP-PRB-NOT-MINE"
		request.save()
		request.reload()
		self.assertNotEqual(request.employee_preboarding, "HR-EMP-PRB-NOT-MINE")

		request.documents = request.documents[:1]
		self.assertRaises(frappe.PermissionError, request.save)

	def test_details_are_checked_only_on_submit(self):
		request = get_request(start_preboarding())
		frappe.set_user(CANDIDATE_EMAIL)

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

	def test_required_documents_block_submit(self):
		request = get_request(start_preboarding())
		frappe.set_user(CANDIDATE_EMAIL)
		fill_mandatory_details(request)
		request.save()

		self.assertRaises(frappe.ValidationError, request.submit_details)

	def test_create_employee_dialog_gets_the_request(self):
		preboarding = start_preboarding()
		request = get_request(preboarding)
		fill_mandatory_details(request)
		request.bank_name = "HDFC Bank"
		request.save()

		employee = make_employee(preboarding.name)
		details = employee.get_onload().employee_details

		self.assertEqual((employee.gender, employee.bank_name), ("Female", "HDFC Bank"))
		self.assertEqual(details["name"], request.name)
		self.assertIn("bank_name", details["fields"])

	def test_employee_from_the_list_fills_only_blank_fields_and_retires_the_request(self):
		preboarding = start_preboarding()
		request = get_request(preboarding)
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
				"company": preboarding.company,
				"job_offer": preboarding.job_offer,
				"bank_name": "State Bank of India",
			}
		).insert()
		employee.reload()

		self.assertEqual(employee.bank_name, "State Bank of India")
		self.assertEqual(employee.cell_number, "+91-9876543210")
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
		preboarding = start_preboarding(as_user=hr_manager)
		request = get_request(preboarding)
		self.assertIn(PREBOARDING_CANDIDATE_ROLE, frappe.get_roles(CANDIDATE_EMAIL))

		fill_mandatory_details(request)
		request.save()
		frappe.set_user(hr_manager)
		make_employee(preboarding.name).insert()

		self.assertFalse(frappe.db.exists("Employee Request", request.name))
		self.assertNotIn(PREBOARDING_CANDIDATE_ROLE, frappe.get_roles(CANDIDATE_EMAIL))


def start_preboarding(as_user=None):
	template = get_test_template()
	template.set(
		"required_documents",
		[
			{"document_name": "PAN Card", "required": 1},
			{"document_name": "Degree Certificate", "required": 0},
		],
	)
	template.save()

	preboarding = create_employee_preboarding(submit=True)
	preboarding.date_of_joining = add_days(getdate(), 7)
	if as_user:
		frappe.set_user(as_user)
	preboarding.create_user("Personal Email", personal_email=CANDIDATE_EMAIL)
	frappe.set_user("Administrator")
	preboarding.reload()
	return preboarding


def get_request(preboarding):
	return frappe.get_doc("Employee Request", {"employee_preboarding": preboarding.name})


def fill_mandatory_details(request):
	request.update({"first_name": "Asha", "gender": "Female", "date_of_birth": "1995-02-01"})


def upload_file(file_name):
	return save_file(file_name, b"test document", None, None, is_private=1)
