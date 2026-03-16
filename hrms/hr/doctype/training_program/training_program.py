# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from frappe.model.document import Document


class TrainingProgram(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		company: DF.Link
		contact_number: DF.Data | None
		description: DF.TextEditor
		status: DF.Literal["Scheduled", "Completed", "Cancelled"]
		supplier: DF.Link | None
		trainer_email: DF.Data | None
		trainer_name: DF.Data | None
		training_program: DF.Data
	# end: auto-generated types

	pass
