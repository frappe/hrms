# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class FullandFinalOutstandingStatement(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		account: DF.Link | None
		amount: DF.Currency
		component: DF.Data
		paid_via_salary_slip: DF.Check
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		reference_document: DF.DynamicLink | None
		reference_document_type: DF.Link | None
		remark: DF.SmallText | None
		status: DF.Literal["Settled", "Unsettled"]
	# end: auto-generated types

	pass
