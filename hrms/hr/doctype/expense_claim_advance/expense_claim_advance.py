# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from frappe.model.document import Document


class ExpenseClaimAdvance(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		advance_account: DF.Link | None
		advance_paid: DF.Currency
		allocated_amount: DF.Currency
		base_advance_paid: DF.Currency
		base_allocated_amount: DF.Currency
		base_unclaimed_amount: DF.Currency
		employee_advance: DF.Link
		exchange_gain_loss: DF.Currency
		exchange_rate: DF.Float
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		payment_entry: DF.Link | None
		payment_entry_reference: DF.Data | None
		posting_date: DF.Date | None
		return_amount: DF.Currency
		unclaimed_amount: DF.Currency
	# end: auto-generated types

	pass
