# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document


class BranchStaffingTemplate(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		branch_type: DF.Data | None
		description: DF.SmallText | None
		is_active: DF.Check
		staffing_details: DF.Table
		template_name: DF.Data
	# end: auto-generated types

	def validate(self):
		self.validate_quantities()
		self.validate_unique_templates()

	def validate_quantities(self):
		for row in self.staffing_details:
			if row.quantity < 1:
				frappe.throw(
					_("Row {0}: Quantity for {1} must be at least 1.").format(
						row.idx, frappe.bold(row.position_template)
					)
				)

	def validate_unique_templates(self):
		"""Each position template should appear at most once; merge quantities otherwise."""
		seen = set()
		for row in self.staffing_details:
			if row.position_template in seen:
				frappe.throw(
					_("Position Template {0} is listed more than once. Combine it into a single row.").format(
						frappe.bold(row.position_template)
					)
				)
			seen.add(row.position_template)

	def total_positions(self) -> int:
		return sum(row.quantity for row in self.staffing_details)
