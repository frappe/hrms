# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import get_link_to_form, now_datetime

from hrms.hr.utils import validate_active_employee


class AssetRequest(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		asset: DF.Link | None
		asset_category: DF.Link | None
		asset_name: DF.Data | None
		company: DF.Link
		department: DF.Link | None
		employee: DF.Link
		employee_name: DF.Data | None
		reason: DF.SmallText | None
		rejection_reason: DF.SmallText | None
		request_type: DF.Literal["Issue", "Return"]
		required_by: DF.Date | None
		status: DF.Literal["Open", "Approved", "Rejected", "Cancelled"]
	# end: auto-generated types

	def onload(self):
		self.set_onload("asset_movement", self.get_asset_movement())

	def validate(self):
		validate_active_employee(self.employee)
		self.validate_status_change()
		if self.request_type == "Return":
			self.validate_return()

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
			frappe.throw(_("Only HR can approve or reject an Asset Request"), frappe.PermissionError)

	def validate_return(self):
		if frappe.db.get_value("Asset", self.asset, "custodian") != self.employee:
			frappe.throw(
				_("{0} does not hold asset {1}").format(
					frappe.bold(self.employee_name or self.employee), frappe.bold(self.asset)
				),
				title=_("Not the Custodian"),
			)
		open_return = frappe.db.exists(
			self.doctype,
			{
				"asset": self.asset,
				"request_type": "Return",
				"docstatus": 0,
				"name": ["!=", self.name or ""],
			},
		)
		if open_return:
			frappe.throw(
				_("Asset {0} already has an open return request {1}").format(
					frappe.bold(self.asset), get_link_to_form(self.doctype, open_return)
				),
				title=_("Open Request Exists"),
			)

	def on_discard(self):
		self.db_set("status", "Cancelled")

	def on_submit(self):
		if self.status not in ("Approved", "Rejected"):
			frappe.throw(_("Approve or reject the request before submitting it"))

	def get_asset_movement(self) -> str | None:
		return frappe.db.get_value(
			"Asset Movement",
			{"reference_doctype": self.doctype, "reference_name": self.name, "docstatus": ["!=", 2]},
			"name",
		)


@frappe.whitelist()
def make_asset_movement(source_name: str, target_doc: str | Document | None = None) -> Document:
	"""The Asset Movement that carries out an approved request: Issue to the employee, or Receipt
	of the asset back from them. The asset manager adds what ERPNext asks for, such as the location."""

	def set_missing_values(source, target):
		target.purpose = "Issue" if source.request_type == "Issue" else "Receipt"
		target.transaction_date = now_datetime()
		target.reference_doctype = source.doctype
		target.reference_name = source.name
		if source.request_type == "Issue":
			target.append("assets", {"to_employee": source.employee})
		else:
			target.append("assets", {"asset": source.asset, "from_employee": source.employee})

	return get_mapped_doc(
		"Asset Request",
		source_name,
		{
			"Asset Request": {
				"doctype": "Asset Movement",
				"field_map": {"company": "company"},
				"validation": {"docstatus": ["=", 1], "status": ["=", "Approved"]},
			}
		},
		target_doc,
		set_missing_values,
	)
