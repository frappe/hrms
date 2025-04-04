# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


# import frappe
from frappe.model.document import Document

import erpnext


class IncomeTaxSlab(Document):
	def validate(self):
		if self.company:
			self.currency = erpnext.get_company_currency(self.company)
