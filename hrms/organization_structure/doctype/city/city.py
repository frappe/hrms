# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class City(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		city_code: DF.Data | None
		city_name: DF.Data
		region: DF.Link
		status: DF.Literal["Active", "Inactive"]
		zone: DF.Link
	# end: auto-generated types

	def validate(self):
		self.validate_geography()

	def validate_geography(self):
		if self.region and frappe.db.get_value("Region", self.region, "status") == "Inactive":
			frappe.throw(_("Region {0} is inactive.").format(frappe.bold(self.region)))

		if not self.zone:
			return

		zone_region = frappe.db.get_value("Zone", self.zone, ["region", "status"], as_dict=True)
		if not zone_region:
			return

		if zone_region.status == "Inactive":
			frappe.throw(_("Zone {0} is inactive.").format(frappe.bold(self.zone)))

		if zone_region.region != self.region:
			frappe.throw(
				_("Zone {0} does not belong to Region {1}.").format(
					frappe.bold(self.zone), frappe.bold(self.region)
				)
			)
