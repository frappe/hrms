# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


# import frappe
from frappe.model.document import Document


class EmployeeTaxExemptionProofSubmissionDetail(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amount: DF.Currency
		attach_proof: DF.Attach | None
		exemption_category: DF.ReadOnly
		exemption_sub_category: DF.Link
		max_amount: DF.Currency
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		type_of_proof: DF.Data
	# end: auto-generated types

	pass
