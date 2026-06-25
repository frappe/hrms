# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Woreda(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		city: DF.Link
		status: DF.Literal["Active", "Inactive"]
		woreda_code: DF.Data | None
		woreda_name: DF.Data
	# end: auto-generated types

	def validate(self):
		self.validate_city_active()

	def validate_city_active(self):
		if self.city and frappe.db.get_value("City", self.city, "status") == "Inactive":
			frappe.throw(_("City {0} is inactive.").format(frappe.bold(self.city)))
