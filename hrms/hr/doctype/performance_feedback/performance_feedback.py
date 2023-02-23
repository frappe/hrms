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
		appraisal.db_update()

	def set_total_score(self):
		total = 0
		for entry in self.kra_rating:
			score = flt(entry.rating) * 5 * flt(entry.per_weightage / 100)
			total += flt(score)

		self.total_score = total

	@frappe.whitelist()
	def set_kras(self):
		if not self.appraisal:
			return

		template = frappe.db.get_value("Appraisal", self.appraisal, "appraisal_template")
		template = frappe.get_doc("Appraisal Template", template)

		self.set("kra_rating", [])
		for kra in template.goals:
			self.append(
				"kra_rating",
				{
					"kra": kra.kra,
					"per_weightage": kra.per_weightage,
				},
			)

		return self
