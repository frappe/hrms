# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from frappe.model.document import Document


class EmployeeDocumentType(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		description: DF.SmallText | None
		document_type: DF.Data
		has_expiry: DF.Check
		has_number: DF.Check
		is_required: DF.Check
	# end: auto-generated types

	pass
