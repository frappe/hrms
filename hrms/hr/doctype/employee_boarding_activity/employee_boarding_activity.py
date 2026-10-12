# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from frappe.model.document import Document


class EmployeeBoardingActivity(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		action: DF.Literal["Manual", "Create User", "Appointment Letter", "Create Employee", "Assign"]
		activity_name: DF.Data
		begin_on: DF.Int
		completed: DF.Check
		depends_on_action: DF.Literal["", "Create User", "Create Employee", "Appointment Letter"]
		description: DF.TextEditor | None
		due_date: DF.Date | None
		duration: DF.Int
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		reference_doctype: DF.Link | None
		reference_name: DF.DynamicLink | None
		required_for_employee_creation: DF.Check
		role: DF.Link | None
		skipped: DF.Check
		status: DF.Literal["", "In Progress", "Stuck"]
		task: DF.Link | None
		task_weight: DF.Float
		todo: DF.Link | None
		user: DF.Link | None
	# end: auto-generated types

	pass
