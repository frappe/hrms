# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from hrms.organization_structure.doctype.position.position import update_occupancy


class PositionAssignment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		employee: DF.Link
		employee_name: DF.Data | None
		end_date: DF.Date | None
		organization_unit: DF.Link | None
		position: DF.Link
		position_name: DF.Data | None
		start_date: DF.Date
		status: DF.Literal["Active", "Inactive"]
	# end: auto-generated types

	def validate(self):
		self.validate_dates()
		self.validate_single_active_assignment()

	def on_update(self):
		self.refresh_position_occupancy()

	def on_trash(self):
		self.refresh_position_occupancy()

	def validate_dates(self):
		if self.end_date and getdate(self.start_date) > getdate(self.end_date):
			frappe.throw(_("Start Date cannot be after End Date."))

	def validate_single_active_assignment(self):
		"""A position can only be actively occupied by one employee at a time."""
		if self.status != "Active":
			return

		conflict = frappe.db.get_value(
			"Position Assignment",
			{
				"position": self.position,
				"status": "Active",
				"name": ["!=", self.name],
			},
			["name", "employee_name"],
			as_dict=True,
		)

		if conflict:
			frappe.throw(
				_("Position {0} is already actively assigned to {1} (Assignment {2}).").format(
					frappe.bold(self.position),
					frappe.bold(conflict.employee_name),
					frappe.bold(conflict.name),
				),
				title=_("Position Already Occupied"),
			)

	def refresh_position_occupancy(self):
		# handle position change on edit: update both old and new positions
		positions = {self.position}
		doc_before_save = self.get_doc_before_save()
		if doc_before_save and doc_before_save.position:
			positions.add(doc_before_save.position)

		for position in positions:
			update_occupancy(position)
