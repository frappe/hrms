# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_link_to_form

from erpnext.setup.doctype.employee.employee import get_employee_emails


class TrainingResult(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.training_result_employee.training_result_employee import TrainingResultEmployee

		amended_from: DF.Link | None
		employee_emails: DF.SmallText | None
		employees: DF.Table[TrainingResultEmployee]
		training_event: DF.Link
	# end: auto-generated types

	def validate(self):
		training_event = frappe.get_doc("Training Event", self.training_event)
		if training_event.docstatus != 1:
			frappe.throw(_("{0} must be submitted").format(_("Training Event")))

		self.validate_duplicate_result()
		self.validate_employees(training_event)
		self.employee_emails = ", ".join(get_employee_emails([d.employee for d in self.employees]))

	def validate_duplicate_result(self):
		existing = frappe.db.exists(
			"Training Result",
			{"training_event": self.training_event, "docstatus": ("<", 2), "name": ("!=", self.name)},
		)
		if existing:
			frappe.throw(
				_("Training Result {0} already exists for Training Event {1}").format(
					get_link_to_form("Training Result", existing), frappe.bold(self.training_event)
				),
				title=_("Duplicate Training Result"),
			)

	def validate_employees(self, training_event):
		attendees = {d.employee for d in training_event.employees}
		seen = set()
		for row in self.employees:
			if row.employee not in attendees:
				frappe.throw(
					_("Row #{0}: Employee {1} is not an attendee of Training Event {2}").format(
						row.idx, frappe.bold(row.employee), frappe.bold(self.training_event)
					)
				)
			if row.employee in seen:
				frappe.throw(
					_("Row #{0}: Duplicate entry for Employee {1}").format(row.idx, frappe.bold(row.employee))
				)
			seen.add(row.employee)

	def on_submit(self):
		training_event = frappe.get_doc("Training Event", self.training_event)
		training_event.event_status = "Completed"
		employees = {e.employee for e in self.employees}
		for row in training_event.employees:
			if row.employee in employees and row.status != "Feedback Submitted":
				row.status = "Completed"

		training_event.save()

	def on_cancel(self):
		training_event = frappe.get_doc("Training Event", self.training_event)
		training_event.event_status = "Scheduled"
		training_event.save()


@frappe.whitelist()
def get_employees(training_event: str):
	frappe.has_permission("Training Event", "read", training_event, throw=True)
	return frappe.get_doc("Training Event", training_event).employees
