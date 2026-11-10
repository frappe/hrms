# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class EmployeeDocument(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		attachment: DF.Attach | None
		document_number: DF.Data | None
		document_type: DF.Link
		due_date: DF.Date | None
		expiry_date: DF.Date | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		remarks: DF.SmallText | None
		status: DF.Literal["Pending", "Submitted", "Verified", "Rejected"]
		verified_on: DF.Date | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Employee Document"
