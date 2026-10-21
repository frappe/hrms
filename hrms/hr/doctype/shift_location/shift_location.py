# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

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
		self.validate_coordinates()
		self.set_geolocation()

	def validate_coordinates(self):
		if self.checkin_radius > 0 and not (self.latitude or self.longitude):
			frappe.throw(_("Latitude and Longitude are required to set a Checkin Radius."))

		if not -90 <= flt(self.latitude) <= 90:
			frappe.throw(_("Latitude must be between -90 and 90."))

		if not -180 <= flt(self.longitude) <= 180:
			frappe.throw(_("Longitude must be between -180 and 180."))

	@frappe.whitelist()
	def set_geolocation(self):
		set_geolocation_from_coordinates(self)
