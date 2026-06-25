# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document


class PositionTemplate(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		description: DF.SmallText | None
		job_category: DF.Link | None
		job_grade: DF.Link | None
		parent_position_template: DF.Link | None
		position_family: DF.Data | None
		template_code: DF.Data
		template_name: DF.Data
	# end: auto-generated types

	def validate(self):
		self.validate_parent_loop()

	def validate_parent_loop(self):
		"""Prevent a template from being its own ancestor (the link is self-referential)."""
		parent = self.parent_position_template
		if not parent:
			return

		if parent == self.name:
			frappe.throw(
				_("A Position Template cannot be its own parent."),
				title=_("Invalid Template Hierarchy"),
			)

		ancestor = parent
		visited = set()
		while ancestor and ancestor not in visited:
			if ancestor == self.name:
				frappe.throw(
					_("Circular reference detected in Position Template hierarchy for {0}.").format(
						frappe.bold(self.name)
					),
					title=_("Invalid Template Hierarchy"),
				)
			visited.add(ancestor)
			ancestor = frappe.db.get_value("Position Template", ancestor, "parent_position_template")
