# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.asset_request.asset_request import make_asset_movement
from hrms.hr.doctype.full_and_final_statement.test_full_and_final_statement import (
	create_asset_movement,
)
from hrms.tests.utils import HRMSTestSuite

USER = "asset_request@example.com"


class TestAssetRequest(HRMSTestSuite):
	def setUp(self):
		self.employee = make_employee(USER, company="_Test Company")
		self.addCleanup(frappe.set_user, "Administrator")

	def make_request(self, **kwargs):
		return frappe.get_doc({"doctype": "Asset Request", "employee": self.employee, **kwargs}).insert()

	def issue_asset(self) -> str:
		"""An asset the employee holds, given to them by an Asset Movement"""
		movement = create_asset_movement(self.employee)
		return frappe.get_doc("Asset Movement", movement).assets[0].asset

	def approve(self, request):
		request.status = "Approved"
		request.submit()

	def test_issue_request_maps_to_an_issue_movement(self):
		category = frappe.db.get_value("Asset", self.issue_asset(), "asset_category")
		request = self.make_request(request_type="Issue", asset_category=category)
		self.approve(request)

		movement = make_asset_movement(request.name)
		self.assertEqual(movement.purpose, "Issue")
		self.assertEqual(
			(movement.reference_doctype, movement.reference_name), (request.doctype, request.name)
		)
		self.assertEqual(movement.assets[0].to_employee, self.employee)

	def test_return_request_maps_to_a_receipt_movement(self):
		asset = self.issue_asset()
		request = self.make_request(request_type="Return", asset=asset)
		self.approve(request)

		movement = make_asset_movement(request.name)
		self.assertEqual(movement.purpose, "Receipt")
		self.assertEqual((movement.assets[0].asset, movement.assets[0].from_employee), (asset, self.employee))

	def test_only_an_approved_request_maps_to_a_movement(self):
		asset = self.issue_asset()
		request = self.make_request(request_type="Return", asset=asset)
		self.assertRaises(frappe.ValidationError, make_asset_movement, request.name)

		request.status = "Rejected"
		request.rejection_reason = "Still needed for the project"
		request.submit()
		self.assertRaises(frappe.ValidationError, make_asset_movement, request.name)

	def test_return_needs_the_asset_held(self):
		asset = self.issue_asset()
		other = make_employee("asset_request_other@example.com", company="_Test Company")
		self.assertRaises(
			frappe.ValidationError,
			frappe.get_doc(
				{"doctype": "Asset Request", "employee": other, "request_type": "Return", "asset": asset}
			).insert,
		)

	def test_one_open_return_per_asset(self):
		asset = self.issue_asset()
		self.make_request(request_type="Return", asset=asset)
		self.assertRaises(frappe.ValidationError, self.make_request, request_type="Return", asset=asset)

	def test_employee_cannot_approve_their_own_request(self):
		asset = self.issue_asset()
		frappe.set_user(USER)
		request = self.make_request(request_type="Return", asset=asset)
		request.status = "Approved"
		self.assertRaises(frappe.PermissionError, request.save)

	def test_employee_is_told_why_their_request_was_rejected(self):
		asset = self.issue_asset()
		frappe.set_user(USER)
		request = self.make_request(request_type="Return", asset=asset)

		frappe.set_user("Administrator")
		request.reload()
		request.status = "Rejected"
		request.rejection_reason = "Still needed for the project"
		request.submit()

		notification = frappe.get_all(
			"Notification Log",
			filters={"for_user": USER, "document_name": request.name},
			fields=["subject", "email_content"],
		)
		self.assertEqual(len(notification), 1)
		self.assertEqual(notification[0].subject, f"Your asset request {request.name} is rejected")
		self.assertEqual(notification[0].email_content, "<p>Reason: Still needed for the project</p>")
