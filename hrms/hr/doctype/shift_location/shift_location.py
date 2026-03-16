# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from hrms.hr.utils import set_geolocation_from_coordinates


class ShiftLocation(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		checkin_radius: DF.Int
		latitude: DF.Float
		location_name: DF.Data
		longitude: DF.Float
	# end: auto-generated types

	def validate(self):
		self.set_geolocation()

	@frappe.whitelist()
	def set_geolocation(self):
		set_geolocation_from_coordinates(self)
