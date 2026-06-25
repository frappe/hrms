# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Zone(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		region: DF.Link
		status: DF.Literal["Active", "Inactive"]
		zone_code: DF.Data | None
		zone_name: DF.Data
	# end: auto-generated types

	def validate(self):
		self.validate_region_active()

	def validate_region_active(self):
		if self.region and frappe.db.get_value("Region", self.region, "status") == "Inactive":
			frappe.throw(
				_("Region {0} is inactive and cannot be linked to a Zone.").format(frappe.bold(self.region))
			)
