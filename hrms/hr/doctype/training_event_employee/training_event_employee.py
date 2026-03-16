# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from frappe.model.document import Document


class TrainingEventEmployee(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		attendance: DF.Literal["Present", "Absent"]
		department: DF.Link | None
		employee: DF.Link | None
		employee_name: DF.ReadOnly | None
		is_mandatory: DF.Check
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		status: DF.Literal["Open", "Invited", "Completed", "Feedback Submitted"]
	# end: auto-generated types

	pass
