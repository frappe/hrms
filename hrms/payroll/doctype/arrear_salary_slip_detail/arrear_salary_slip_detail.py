# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class ArrearSalarySlipDetail(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amount: DF.Float
		arrear_type: DF.Literal["Earning", "Deduction", "Accrual"]
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		salary_component: DF.Link
		salary_slip: DF.Link
	# end: auto-generated types

	pass
