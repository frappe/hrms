# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_link_to_form

from erpnext.setup.doctype.employee.employee import get_employee_emails


class TrainingResult(Document):
	def validate(self):
		training_event = frappe.get_doc("Training Event", self.training_event)
		if training_event.docstatus != 1:
			frappe.throw(_("{0} must be submitted").format(_("Training Event")))

		self.validate_duplicate_result()
		self.employee_emails = ", ".join(get_employee_emails([d.employee for d in self.employees]))

	def validate_duplicate_result(self):
		if result := frappe.db.exists(
			"Training Result",
			{"training_event": self.training_event, "docstatus": ("!=", 2), "name": ("!=", self.name)},
		):
			frappe.throw(
				_("Training Result {0} already exists for Training Event {1}").format(
					get_link_to_form("Training Result", result), frappe.bold(self.training_event)
				),
				frappe.UniqueValidationError,
			)

	def on_submit(self):
		training_event = frappe.get_doc("Training Event", self.training_event)
		training_event.status = "Completed"
		for e in self.employees:
			for e1 in training_event.employees:
				if e1.employee == e.employee:
					e1.status = "Completed"
					break

		training_event.save()


@frappe.whitelist()
def get_employees(training_event: str):
	frappe.has_permission("Training Event", "read", training_event, throw=True)
	return frappe.get_doc("Training Event", training_event).employees
