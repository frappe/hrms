# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _, bold
from frappe.model.document import Document
from frappe.utils import cstr, getdate

RESOLUTION_FIELDS = (
	"status",
	"cause_of_grievance",
	"resolved_by",
	"resolution_date",
	"resolution_detail",
	"employee_responsible",
)
HR_ROLES = {"HR User", "HR Manager", "System Manager"}


class EmployeeGrievance(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		associated_document: DF.DynamicLink | None
		associated_document_type: DF.Link | None
		cause_of_grievance: DF.Text | None
		date: DF.Date
		description: DF.Text
		designation: DF.Link | None
		employee_name: DF.Data | None
		employee_responsible: DF.Link | None
		grievance_against: DF.DynamicLink
		grievance_against_party: DF.Link
		grievance_type: DF.Link
		raised_by: DF.Link
		reports_to: DF.Link | None
		resolution_date: DF.Date | None
		resolution_detail: DF.SmallText | None
		resolved_by: DF.Link | None
		status: DF.Literal["Open", "Investigated", "Resolved", "Invalid", "Cancelled"]
		subject: DF.Data
	# end: auto-generated types

	def validate(self):
		self.validate_grievance_against()
		self.validate_resolution_date()
		self.validate_resolution_changes()

	def validate_grievance_against(self):
		if self.grievance_against_party == "Employee" and self.grievance_against == self.raised_by:
			frappe.throw(_("An employee cannot raise a grievance against themselves"))

	def validate_resolution_date(self):
		if self.resolution_date and getdate(self.resolution_date) < getdate(self.date):
			frappe.throw(_("Resolution Date cannot be before the grievance Date"))

	def validate_resolution_changes(self):
		if HR_ROLES.intersection(frappe.get_roles()):
			return

		before = self.get_doc_before_save() or frappe.new_doc(self.doctype)
		changed = [
			self.meta.get_label(fieldname)
			for fieldname in RESOLUTION_FIELDS
			if cstr(self.get(fieldname)) != cstr(before.get(fieldname))
		]
		if changed:
			frappe.throw(
				_("Only HR can update {0}").format(", ".join(_(label) for label in changed)),
				frappe.PermissionError,
			)

	def on_submit(self):
		if self.status not in ["Invalid", "Resolved"]:
			frappe.throw(
				_("Only Employee Grievance with status {0} or {1} can be submitted").format(
					bold(_("Invalid")), bold(_("Resolved"))
				)
			)

	def on_cancel(self):
		self.db_set("status", "Cancelled")

	def on_discard(self):
		self.db_set("status", "Cancelled")
