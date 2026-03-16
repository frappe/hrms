# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from frappe.model.document import Document

# import frappe
import erpnext


class IncomeTaxSlab(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.payroll.doctype.income_tax_slab_other_charges.income_tax_slab_other_charges import (
			IncomeTaxSlabOtherCharges,
		)
		from hrms.payroll.doctype.taxable_salary_slab.taxable_salary_slab import TaxableSalarySlab

		allow_tax_exemption: DF.Check
		amended_from: DF.Link | None
		company: DF.Link | None
		currency: DF.Link
		disabled: DF.Check
		effective_from: DF.Date
		other_taxes_and_charges: DF.Table[IncomeTaxSlabOtherCharges]
		slabs: DF.Table[TaxableSalarySlab]
		standard_tax_exemption_amount: DF.Currency
		tax_relief_limit: DF.Currency
	# end: auto-generated types

	def validate(self):
		if self.company:
			self.currency = erpnext.get_company_currency(self.company)
