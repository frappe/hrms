# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class PerformanceFeedback(Document):
	def validate(self):
		self.set_total_score()

	def on_update(self):
		self.update_feedback_in_appraisal()

	def update_feedback_in_appraisal(self):
		if not self.appraisal:
			return

		appraisal = frappe.get_doc("Appraisal", self.appraisal)
		appraisal.calculate_avg_feedback_score()
		appraisal.db_update_all()

	def set_total_score(self):
		total = 0
		for entry in self.kra_rating:
			score = flt(entry.rating) * 5 * flt(entry.per_weightage / 100)
			total += flt(score)

		self.total_score = total


@frappe.whitelist()
def get_kra(employee):
	kra_template = frappe.db.get_value("Appraisal", {"employee": employee}, "kra_template")
	return frappe.get_doc("Appraisal Template", kra_template)
