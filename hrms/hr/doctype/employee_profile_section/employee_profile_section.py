# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class EmployeeProfileSection(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		content: DF.LongText | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		section_type: DF.Literal["Cover", "Headline", "Text", "Tags", "Photos", "Links"]
		title: DF.Data | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Employee Profile Section"
