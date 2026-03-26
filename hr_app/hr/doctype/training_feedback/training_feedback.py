# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document


class TrainingFeedback(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		course: DF.Data | None
		department: DF.Link | None
		employee: DF.Link
		employee_name: DF.ReadOnly | None
		event_name: DF.Data | None
		feedback: DF.Text
		trainer_name: DF.Data | None
		training_event: DF.Link
	# end: auto-generated types

	def validate(self):
		training_event = frappe.get_doc("Training Event", self.training_event)
		if training_event.docstatus != 1:
			frappe.throw(_("{0} must be submitted").format(_("Training Event")))

		emp_event_details = frappe.db.get_value(
			"Training Event Employee",
			{"parent": self.training_event, "employee": self.employee},
			["name", "attendance"],
			as_dict=True,
		)

		if not emp_event_details:
			frappe.throw(
				_("Employee {0} not found in Training Event Participants.").format(
					frappe.bold(self.employee_name)
				)
			)

		if emp_event_details.attendance == "Absent":
			frappe.throw(_("Feedback cannot be recorded for an absent Employee."))

	def on_submit(self):
		employee = frappe.db.get_value(
			"Training Event Employee", {"parent": self.training_event, "employee": self.employee}
		)

		if employee:
			frappe.db.set_value("Training Event Employee", employee, "status", "Feedback Submitted")

	def on_cancel(self):
		employee = frappe.db.get_value(
			"Training Event Employee", {"parent": self.training_event, "employee": self.employee}
		)

		if employee:
			frappe.db.set_value("Training Event Employee", employee, "status", "Completed")
