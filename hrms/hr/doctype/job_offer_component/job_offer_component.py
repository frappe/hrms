# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from frappe.model.document import Document


class JobOfferComponent(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		currency: DF.Link | None
		fixed_components: DF.Data
		is_summary: DF.Check
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		per_cycle: DF.Currency
		yearly: DF.Currency
	# end: auto-generated types

	pass
