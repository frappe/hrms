# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class FullandFinalAsset(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		account: DF.Link | None
		action: DF.Literal["Return", "Recover Cost"]
		actual_cost: DF.Currency
		asset_name: DF.Data | None
		cost: DF.Currency
		date: DF.Datetime | None
		description: DF.SmallText | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		reference: DF.Link
		status: DF.Literal["Owned", "Returned"]
	# end: auto-generated types

	pass
