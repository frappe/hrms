# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


# import frappe
from frappe.model.document import Document


class SalarySlipLeave(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		available_leaves: DF.Float
		expired_leaves: DF.Float
		leave_type: DF.Link | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		pending_leaves: DF.Float
		total_allocated_leaves: DF.Float
		used_leaves: DF.Float
	# end: auto-generated types

	pass
