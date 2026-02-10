# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document


class TrainingFeedback(Document):
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

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_training_event_employees(doctype, txt, searchfield, start, page_len, filters):
	if not filters.get("training_event"):
		return []

	tee = frappe.qb.DocType("Training Event Employee")
	emp = frappe.qb.DocType("Employee")

	query = (
		frappe.qb.from_(tee)
		.join(emp)
		.on(tee.employee == emp.name)
		.select(tee.employee, emp.employee_name)
		.where((tee.parent == filters.get("training_event")) & (tee.attendance != "Absent"))
	)

	if txt:
		query = query.where(
			(emp.name.like(f"%{txt}%")) | (emp.employee_name.like(f"%{txt}%"))
		)

	return query.orderby(emp.employee_name).limit(page_len).offset(start).run()
