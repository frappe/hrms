# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_link_to_form

from hrms.hr.utils import validate_active_employee


class BankDetailsChangeRequest(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		bank_ac_no: DF.Data
		bank_name: DF.Data
		company: DF.Link
		department: DF.Link | None
		employee: DF.Link
		employee_name: DF.Data | None
		iban: DF.Data | None
		ifsc_code: DF.Data | None
		proof: DF.Attach
		reason: DF.SmallText | None
		rejection_reason: DF.SmallText | None
		status: DF.Literal["Open", "Approved", "Rejected", "Cancelled"]
	# end: auto-generated types

	def validate(self):
		validate_active_employee(self.employee)
		self.validate_status_change()
		self.validate_open_request()

	def validate_status_change(self):
		# a request is cancelled by discarding it, which keeps it, as Cancelled
		if self.status == "Cancelled":
			frappe.throw(_("Set the status to Open, or discard the request to cancel it"))
		if self.status == "Rejected" and not (self.rejection_reason or "").strip():
			frappe.throw(
				_("Give a rejection reason, so {0} knows what to do next").format(
					frappe.bold(self.employee_name or self.employee)
				),
				title=_("Rejection Reason Missing"),
			)
		if self.status in ("Approved", "Rejected") and not frappe.has_permission(
			self.doctype, "submit", self
		):
			frappe.throw(
				_("Only HR can approve or reject a Bank Details Change Request"), frappe.PermissionError
			)

	def validate_open_request(self):
		open_request = frappe.db.exists(
			self.doctype,
			{
				"employee": self.employee,
				"docstatus": 0,
				"name": ["!=", self.name or ""],
			},
		)
		if open_request:
			frappe.throw(
				_("{0} already has an open request {1}").format(
					frappe.bold(self.employee_name or self.employee),
					get_link_to_form(self.doctype, open_request),
				),
				title=_("Open Request Exists"),
			)

	def on_discard(self):
		self.db_set("status", "Cancelled")

	def on_submit(self):
		if self.status not in ("Approved", "Rejected"):
			frappe.throw(_("Approve or reject the request before submitting it"))
		if self.status == "Approved":
			self.update_employee()

	def update_employee(self):
		"""The approved details become the employee's salary account. Saved as the approver, so
		their Employee permission applies and the Employee keeps a Version of the change."""
		employee = frappe.get_doc("Employee", self.employee)
		employee.salary_mode = "Bank"
		employee.bank_name = self.bank_name
		employee.bank_ac_no = self.bank_ac_no
		employee.iban = self.iban
		# the India regional setup adds it
		if employee.meta.has_field("ifsc_code"):
			employee.ifsc_code = self.ifsc_code
		employee.save()
