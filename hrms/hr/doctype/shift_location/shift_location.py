# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from hrms.hr.utils import set_geolocation_from_coordinates


class ShiftLocation(Document):
	def validate(self):
		self.set_geolocation()

	@frappe.whitelist()
	def set_geolocation(self):
		set_geolocation_from_coordinates(self)
