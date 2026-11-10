# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from unittest.mock import patch

import frappe
from frappe.utils import get_fullname, getdate

from erpnext.assets.doctype.asset.test_asset import create_asset_category
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.page.employee_profile.employee_profile import (
	get_bank_number,
	get_profile,
	remove_document,
	request_asset,
	request_bank_details_change,
	request_document,
	review_document,
	review_request,
	save_details,
	save_sections,
	upload_document,
	withdraw_request,
)
from hrms.tests.test_utils import create_company
from hrms.tests.utils import HRMSTestSuite
from hrms.utils.holiday_list import get_holiday_list_for_employee

SELF = "profile_self@example.com"
COLLEAGUE = "profile_colleague@example.com"
HR = "profile_hr@example.com"


def upload(file_name: str) -> str:
	"""A file the session user uploads from their profile, attached to nothing yet"""
	return (
		frappe.get_doc({"doctype": "File", "file_name": file_name, "content": b"test", "is_private": 1})
		.insert()
		.file_url
	)


def make_asset_category() -> str:
	if not frappe.db.exists("Asset Category", "Computers"):
		create_asset_category()
	return "Computers"


class TestEmployeeProfile(HRMSTestSuite):
	def setUp(self):
		# colleagues see each other's profiles where the organizational chart is open to them
		self.enterContext(self.change_settings("HR Settings", {"show_org_chart_to_all_employees": 1}))
		self.employee = make_employee(SELF, company="_Test Company")
		self.colleague = make_employee(COLLEAGUE, company="_Test Company")
		# HR, who sees every employee: no user permission on their own record
		self.hr = make_employee(HR, company="_Test Company", create_user_permission=0)
		frappe.get_doc("User", HR).add_roles("HR User", "HR Manager")
		self.category = make_asset_category()
		self.addCleanup(frappe.set_user, "Administrator")

	def make_document_type(self, name: str, **kwargs):
		if not frappe.db.exists("Employee Document Type", name):
			frappe.get_doc({"doctype": "Employee Document Type", "document_type": name, **kwargs}).insert()

	def test_colleague_sees_the_public_part_only(self):
		frappe.set_user(COLLEAGUE)
		profile = get_profile(self.employee)
		self.assertNotIn("private", profile)
		self.assertNotIn("options", profile)
		self.assertFalse(profile["can_edit"])

	def test_self_sees_and_edits_their_own(self):
		frappe.set_user(SELF)
		profile = get_profile()
		self.assertEqual(profile["card"]["id"], self.employee)
		self.assertTrue(profile["can_edit"])
		self.assertIn("documents", profile["private"])

	def test_other_company_is_refused(self):
		other = make_employee(
			"profile_other@example.com",
			company=create_company("Test Profile Other Company", abbr="_TPOC").name,
		)
		frappe.set_user(COLLEAGUE)
		self.assertRaises(frappe.PermissionError, get_profile, other)

	def test_personal_details_take_only_the_listed_fields(self):
		frappe.set_user(SELF)
		self.assertRaises(frappe.ValidationError, save_details, {"ctc": 1})
		self.assertRaises(frappe.ValidationError, save_details, {"cell_number": "12"})
		# HR keeps the employment and bank details
		self.assertRaises(frappe.ValidationError, save_details, {"notice_number_of_days": 30})
		self.assertRaises(frappe.ValidationError, save_details, {"bank_ac_no": "123456"})

		save_details({"date_of_birth": "1991-05-20", "cell_number": "+91 98765 43210"})
		employee = frappe.db.get_value(
			"Employee", self.employee, ["date_of_birth", "date_of_retirement", "cell_number"], as_dict=True
		)
		self.assertEqual(employee.date_of_birth, getdate("1991-05-20"))
		# as the Employee form does, from the retirement age in HR Settings
		self.assertEqual(employee.date_of_retirement.month, 5)
		self.assertEqual(employee.cell_number, "+91 98765 43210")

	def test_sections_take_only_own_files(self):
		frappe.set_user("Administrator")
		someone_elses = upload("theirs.png")
		frappe.set_user(SELF)
		photos = {"type": "Photos", "title": "Photos", "content": [{"image": someone_elses}]}
		self.assertRaises(frappe.ValidationError, save_sections, [photos])

	def test_document_upload_waits_for_hr(self):
		frappe.get_doc(
			{
				"doctype": "Employee Document Type",
				"document_type": "Test PAN",
				"is_required": 1,
				"has_number": 1,
			}
		).insert()
		frappe.set_user(SELF)
		self.assertEqual(
			{
				doc["status"]
				for doc in get_profile()["private"]["documents"]
				if doc["document_type"] == "Test PAN"
			},
			{"Missing"},
		)

		file_url = upload("pan.png")
		documents = upload_document("Test PAN", file_url, document_number="ABCDE1234F")["documents"]
		row = next(doc for doc in documents if doc["document_type"] == "Test PAN")
		self.assertEqual((row["status"], row["document_number"]), ("Submitted", "ABCDE1234F"))
		self.assertEqual(
			frappe.db.get_value("File", {"file_url": file_url}, "attached_to_name"), self.employee
		)
		# a file already in use is not taken again
		self.assertRaises(frappe.ValidationError, upload_document, "Test PAN", file_url)

	def test_bank_change_is_requested_for_own_record(self):
		frappe.set_user(SELF)
		proof = upload("cheque.png")
		request = request_bank_details_change(
			{"bank_name": "Test Bank", "bank_ac_no": "001122334455", "proof": proof}
		)["bank_request"]
		self.assertEqual(request["bank_ac_no"], "••••4455")
		self.assertEqual(
			frappe.db.get_value("Bank Details Change Request", request["name"], "employee"), self.employee
		)
		self.assertEqual(
			frappe.db.get_value("File", {"file_url": proof}, ["attached_to_doctype", "attached_to_name"]),
			("Bank Details Change Request", request["name"]),
		)
		# the employee's own account stays until HR approves
		self.assertIsNone(frappe.db.get_value("Employee", self.employee, "bank_ac_no"))

	def test_withdraw_cancels_only_own_requests(self):
		frappe.set_user(SELF)
		request = request_bank_details_change(
			{"bank_name": "Test Bank", "bank_ac_no": "001122334455", "proof": upload("cheque.png")}
		)["bank_request"]

		frappe.set_user(COLLEAGUE)
		self.assertRaises(
			frappe.PermissionError, withdraw_request, "Bank Details Change Request", request["name"]
		)
		self.assertRaises(frappe.ValidationError, withdraw_request, "Employee", self.employee)

		frappe.set_user(SELF)
		self.assertIsNone(withdraw_request("Bank Details Change Request", request["name"])["bank_request"])
		# discarded, as a draft is: kept, but no longer a draft
		self.assertEqual(
			frappe.db.get_value("Bank Details Change Request", request["name"], ["docstatus", "status"]),
			(2, "Cancelled"),
		)

	def test_open_requests_are_changed_until_hr_decides(self):
		frappe.set_user(SELF)
		request = request_bank_details_change(
			{"bank_name": "Test Bank", "bank_ac_no": "001122334455", "proof": upload("cheque.png")}
		)["bank_request"]
		proof = frappe.db.get_value("Bank Details Change Request", request["name"], "proof")

		# the number shows only its end, so leaving it empty keeps it, and so does the proof
		changed = request_bank_details_change(
			{"bank_name": "Other Bank", "bank_ac_no": "", "proof": proof, "reason": "New branch"},
			request["name"],
		)["bank_request"]
		self.assertEqual(changed["name"], request["name"])
		self.assertEqual(
			frappe.db.get_value(
				"Bank Details Change Request", request["name"], ["bank_name", "bank_ac_no", "reason"]
			),
			("Other Bank", "001122334455", "New branch"),
		)

		asset = request_asset({"request_type": "Issue", "asset_category": self.category})
		asset = asset["asset_requests"][0]["name"]
		request_asset({"asset_category": self.category, "reason": "For travel"}, asset)
		self.assertEqual(frappe.db.get_value("Asset Request", asset, "reason"), "For travel")

		frappe.set_user(COLLEAGUE)
		self.assertRaises(frappe.PermissionError, request_asset, {"asset_category": self.category}, asset)

		frappe.set_user(HR)
		review_request("Asset Request", asset, "Rejected", "Not in this quarter's budget")
		frappe.set_user(SELF)
		self.assertRaises(frappe.PermissionError, request_asset, {"asset_category": self.category}, asset)

	def test_own_upload_is_removed_until_hr_verifies_it(self):
		self.make_document_type("Test Passport", has_number=1)
		self.make_document_type("Test Aadhaar", is_required=1)

		def statuses():
			return {doc["document_type"]: doc["status"] for doc in get_profile()["private"]["documents"]}

		frappe.set_user(SELF)
		upload_document("Test Passport", upload("passport.png"), document_number="P123")
		upload_document("Test Aadhaar", upload("aadhaar.png"))
		# one added by mistake goes, and a required one is asked for again
		remove_document("Test Passport")
		remove_document("Test Aadhaar")
		self.assertNotIn("Test Passport", statuses())
		self.assertEqual(statuses()["Test Aadhaar"], "Missing")

		upload_document("Test Passport", upload("passport.png"), document_number="P123")
		frappe.set_user(COLLEAGUE)
		self.assertRaises(frappe.PermissionError, remove_document, "Test Passport", self.employee)
		# the same refusal for a document the employee does not have, so it tells nothing
		self.assertRaises(frappe.PermissionError, remove_document, "Test Aadhaar", self.employee)

		frappe.set_user(HR)
		review_document(self.employee, "Test Passport", "Verified")
		frappe.set_user(SELF)
		self.assertRaises(frappe.PermissionError, remove_document, "Test Passport")
		# a newer upload of a verified document is not taken back either, as that would lose both
		upload_document("Test Passport", upload("passport-new.png"), document_number="P456")
		self.assertEqual(statuses()["Test Passport"], "Submitted")
		self.assertRaises(frappe.PermissionError, remove_document, "Test Passport")
		frappe.set_user(HR)
		remove_document("Test Passport", self.employee)
		frappe.set_user(SELF)
		self.assertNotIn("Test Passport", statuses())

	def test_employee_cannot_change_document_types(self):
		frappe.set_user(SELF)
		self.assertRaises(
			frappe.PermissionError,
			frappe.get_doc({"doctype": "Employee Document Type", "document_type": "Test Mine"}).insert,
		)

	def test_hr_edits_the_private_part(self):
		frappe.set_user(HR)
		profile = get_profile(self.employee)
		self.assertTrue(profile["can_manage"])
		self.assertFalse(profile["can_edit"], "the public part stays the employee's own")
		self.assertIn("employment_type", profile["options"])

		card = save_details(
			{"notice_number_of_days": "30", "bank_name": "Test Bank", "bank_ac_no": "001122334455"},
			employee=self.employee,
		)["private"]
		self.assertEqual(card["employment"]["notice_number_of_days"], 30)
		self.assertEqual(card["bank"]["bank_ac_no"], "••••4455")
		self.assertEqual(frappe.db.get_value("Employee", self.employee, "salary_mode"), "Bank")
		self.assertRaises(
			frappe.ValidationError, save_details, {"notice_number_of_days": "a month"}, self.employee
		)

		# the holiday list in use comes from Holiday List Assignment, so it is not set here
		self.assertEqual(
			card["employment"]["holiday_list"],
			get_holiday_list_for_employee(self.employee, raise_exception=False),
		)
		self.assertRaises(frappe.ValidationError, save_details, {"holiday_list": "Any List"}, self.employee)

	def test_colleague_cannot_edit_another_employee(self):
		frappe.set_user(COLLEAGUE)
		self.assertRaises(
			frappe.PermissionError, save_details, {"cell_number": "+91 98765 43210"}, self.employee
		)
		self.assertRaises(frappe.PermissionError, request_document, self.employee, "Test Degree")

	def test_hr_reviews_requests_but_not_their_own(self):
		frappe.set_user(SELF)
		request = request_bank_details_change(
			{"bank_name": "Test Bank", "bank_ac_no": "001122334455", "proof": upload("cheque.png")}
		)["bank_request"]
		self.assertRaises(
			frappe.PermissionError, review_request, "Bank Details Change Request", request["name"], "Approved"
		)

		frappe.set_user(HR)
		self.assertTrue(get_profile(self.employee)["can_review"]["Bank Details Change Request"])
		self.assertIsNone(
			review_request("Bank Details Change Request", request["name"], "Approved")["bank_request"]
		)
		self.assertEqual(frappe.db.get_value("Employee", self.employee, "bank_ac_no"), "001122334455")
		# a decided request is closed
		self.assertRaises(
			frappe.ValidationError, review_request, "Bank Details Change Request", request["name"], "Rejected"
		)

		own = request_asset({"request_type": "Issue", "asset_category": self.category})
		own = own["asset_requests"][0]["name"]
		self.assertFalse(get_profile()["can_review"]["Asset Request"])
		self.assertRaises(frappe.PermissionError, review_request, "Asset Request", own, "Approved")

	def test_rejected_requests_show_with_the_reason(self):
		frappe.set_user(SELF)
		bank = request_bank_details_change(
			{"bank_name": "Test Bank", "bank_ac_no": "001122334455", "proof": upload("cheque.png")}
		)["bank_request"]["name"]
		asset = request_asset({"request_type": "Issue", "asset_category": self.category})
		asset = asset["asset_requests"][0]["name"]

		frappe.set_user(HR)
		# a rejection says why
		self.assertRaises(frappe.ValidationError, review_request, "Asset Request", asset, "Rejected")
		self.assertRaises(frappe.ValidationError, review_request, "Asset Request", asset, "Rejected", " ")
		review_request("Asset Request", asset, "Rejected", "Not in this quarter's budget")
		review_request("Bank Details Change Request", bank, "Rejected", "The cheque is not readable")

		frappe.set_user(SELF)
		private = get_profile()["private"]
		row = next(row for row in private["asset_requests"] if row["name"] == asset)
		self.assertEqual(
			(row["status"], row["rejection_reason"]), ("Rejected", "Not in this quarter's budget")
		)
		self.assertEqual(
			(private["bank_decided"]["status"], private["bank_decided"]["rejection_reason"]),
			("Rejected", "The cheque is not readable"),
		)
		self.assertEqual(private["bank_decided"]["bank_ac_no"], "••••4455")

		# a new request takes its place
		bank = request_bank_details_change(
			{"bank_name": "Test Bank", "bank_ac_no": "001122334466", "proof": upload("cheque2.png")}
		)["bank_request"]["name"]
		self.assertIsNone(get_profile()["private"]["bank_decided"])

		# an approved change keeps showing, with who approved it
		frappe.set_user(HR)
		review_request("Bank Details Change Request", bank, "Approved")
		frappe.set_user(SELF)
		decided = get_profile()["private"]["bank_decided"]
		self.assertEqual((decided["name"], decided["status"]), (bank, "Approved"))
		# the approver's name, not the viewer's
		self.assertEqual(decided["decided_by"], get_fullname(HR))

	def test_whole_bank_number_for_the_employee_and_hr_only(self):
		frappe.set_user(SELF)
		request = request_bank_details_change(
			{"bank_name": "Test Bank", "bank_ac_no": "001122334455", "proof": upload("cheque.png")}
		)["bank_request"]["name"]
		self.assertEqual(get_bank_number(self.employee, request)["bank_ac_no"], "001122334455")

		frappe.set_user(HR)
		# each look is kept in the Access Log, which Frappe writes after the request
		with patch("hrms.hr.page.employee_profile.employee_profile.make_access_log") as access_log:
			self.assertEqual(get_bank_number(self.employee, request)["bank_ac_no"], "001122334455")
		access_log.assert_called_once_with(
			doctype="Bank Details Change Request", document=request, method="get_bank_number"
		)

		frappe.set_user(COLLEAGUE)
		self.assertRaises(frappe.PermissionError, get_bank_number, self.employee)
		self.assertRaises(frappe.PermissionError, get_bank_number, self.employee, request)
		# a request is read only through its own employee
		self.assertRaises(frappe.PermissionError, get_bank_number, self.colleague, request)

	def test_approved_asset_request_waits_for_its_movement(self):
		frappe.set_user(SELF)
		request = request_asset({"request_type": "Issue", "asset_category": self.category})
		request = request["asset_requests"][0]["name"]

		frappe.set_user(HR)
		requests = review_request("Asset Request", request, "Approved")["asset_requests"]
		self.assertEqual([(r.name, r.status) for r in requests], [(request, "Approved")])

	def test_hr_checks_and_asks_for_documents(self):
		self.make_document_type("Test Degree", is_required=1)
		frappe.set_user(SELF)
		upload_document("Test Degree", upload("degree.png"))
		self.assertRaises(frappe.PermissionError, review_document, self.employee, "Test Degree", "Verified")

		frappe.set_user(HR)
		documents = review_document(self.employee, "Test Degree", "Rejected", "Blurred")["documents"]
		row = next(doc for doc in documents if doc["document_type"] == "Test Degree")
		self.assertEqual((row["status"], row["remarks"]), ("Rejected", "Blurred"))

		documents = request_document(self.employee, "Test Degree", "2030-01-31")["documents"]
		row = next(doc for doc in documents if doc["document_type"] == "Test Degree")
		self.assertEqual((row["status"], row["due_date"]), ("Pending", getdate("2030-01-31")))

		# one HR uploads for the employee counts at once
		documents = upload_document("Test Degree", upload("degree-2.png"), employee=self.employee)
		row = next(doc for doc in documents["documents"] if doc["document_type"] == "Test Degree")
		self.assertEqual(row["status"], "Verified")
