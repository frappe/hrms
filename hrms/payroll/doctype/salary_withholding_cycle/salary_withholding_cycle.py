# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class SalaryWithholdingCycle(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from_date: DF.Date
		is_salary_released: DF.Check
		journal_entry: DF.Link | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		to_date: DF.Date
	# end: auto-generated types

	pass
