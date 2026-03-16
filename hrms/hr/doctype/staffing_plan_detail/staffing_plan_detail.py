# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from frappe.model.document import Document


class StaffingPlanDetail(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		current_count: DF.Int
		current_openings: DF.Int
		designation: DF.Link
		estimated_cost_per_position: DF.Currency
		number_of_positions: DF.Int
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		total_estimated_cost: DF.Currency
		vacancies: DF.Int
	# end: auto-generated types

	pass
