# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


# import frappe
from frappe.model.document import Document


class SalarySlipLoan(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		interest_amount: DF.Currency
		interest_income_account: DF.Link | None
		loan: DF.Link
		loan_account: DF.Link | None
		loan_product: DF.Link | None
		loan_repayment_entry: DF.Link | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		principal_amount: DF.Currency
		total_payment: DF.Currency
	# end: auto-generated types

	pass
