# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _, bold
from frappe.model.document import Document


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

	def on_submit(self):
		if self.status not in ["Invalid", "Resolved"]:
			frappe.throw(
				_("Only Employee Grievance with status {0} or {1} can be submitted").format(
					bold(_("Invalid")), bold(_("Resolved"))
				)
			)

	def on_discard(self):
		self.db_set("status", "Cancelled")
