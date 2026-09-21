# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class EmployeeOnboardingAssignment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		master: DF.Literal["Holiday List", "Leave Policy", "Salary Structure", "Shift Type", "Shift Schedule"]
		offer_value: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		reference_doctype: DF.Link | None
		reference_name: DF.DynamicLink | None
		status: DF.Literal["Pending", "Assigned", "Skipped"]
	# end: auto-generated types

	pass
