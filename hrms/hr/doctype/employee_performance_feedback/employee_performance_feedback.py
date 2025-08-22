# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_link_to_form

from hrms.hr.doctype.appraisal_cycle.appraisal_cycle import validate_active_appraisal_cycle
from hrms.hr.utils import validate_active_employee
from hrms.mixins.appraisal import AppraisalMixin


class EmployeePerformanceFeedback(Document, AppraisalMixin):
	def validate(self):
		validate_active_appraisal_cycle(self.appraisal_cycle)

		self.validate_employee()
		self.validate_appraisal()
		self.validate_total_weightage("feedback_ratings", "Feedback Ratings")
		self.set_total_score()

	def on_submit(self):
		self.update_avg_feedback_score_in_appraisal()

	def on_cancel(self):
		self.update_avg_feedback_score_in_appraisal()

	def validate_employee(self):
		if self.employee == self.reviewer:
			frappe.throw(
				_("Employees cannot give feedback to themselves. Use {0} instead: {1}").format(
					frappe.bold(_("Self Appraisal")), get_link_to_form("Appraisal", self.appraisal)
				)
			)

		validate_active_employee(self.employee)
		validate_active_employee(self.reviewer)

	def validate_appraisal(self):
		employee = frappe.db.get_value("Appraisal", self.appraisal, "employee")

		if employee != self.employee:
			frappe.throw(
				_("Appraisal {0} does not belong to Employee {1}").format(self.appraisal, self.employee)
			)

	def set_total_score(self):
		total = 0
		for entry in self.feedback_ratings:
			score = flt(entry.rating) * 5 * flt(entry.per_weightage / 100)
			total += flt(score)

		self.total_score = flt(total, self.precision("total_score"))

	def update_avg_feedback_score_in_appraisal(self):
		if not self.appraisal:
			return

		appraisal = frappe.get_doc("Appraisal", self.appraisal)
		appraisal.calculate_avg_feedback_score(update=True)

	@frappe.whitelist()
	def set_feedback_criteria(self):
		if not self.appraisal:
			return

		template = frappe.db.get_value("Appraisal", self.appraisal, "appraisal_template")
		template = frappe.get_doc("Appraisal Template", template)

		self.set("feedback_ratings", [])
		for entry in template.rating_criteria:
			self.append(
				"feedback_ratings",
				{
					"criteria": entry.criteria,
					"per_weightage": entry.per_weightage,
				},
			)

		return self
