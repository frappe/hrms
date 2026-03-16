# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class OvertimeDetails(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		date: DF.Date
		maximum_overtime_hours_allowed: DF.Float
		overtime_duration: DF.Float
		overtime_type: DF.Link
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		reference_document: DF.Link | None
		standard_working_hours: DF.Float
	# end: auto-generated types

	pass
