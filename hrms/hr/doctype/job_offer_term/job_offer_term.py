# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt


from frappe.model.document import Document


class JobOfferTerm(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		offer_term: DF.Link
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		value: DF.SmallText
	# end: auto-generated types

	pass
