# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class EmployeeTaxExemptionSubCategory(Document):
<<<<<<< HEAD
=======
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		description: DF.SmallText | None
		exemption_category: DF.Link
		is_active: DF.Check
		max_amount: DF.Currency
	# end: auto-generated types

>>>>>>> dee44d5b3 (feat(minor): description field for exemption categories and sub categories.)
	def validate(self):
		category_max_amount = frappe.db.get_value(
			"Employee Tax Exemption Category", self.exemption_category, "max_amount"
		)
		if flt(self.max_amount) > flt(category_max_amount):
			frappe.throw(
				_(
					"Max Exemption Amount cannot be greater than maximum exemption amount {0} of Tax Exemption Category {1}"
				).format(category_max_amount, self.exemption_category)
			)
