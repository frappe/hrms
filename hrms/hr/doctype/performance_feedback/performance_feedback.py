# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class PerformanceFeedback(Document):
	def validate(self):
		total = 0
		for entry in self.kra_rating:
			score = flt(entry.rating) * 5 * flt(entry.per_weightage / 100)
			total += flt(score)

		self.total_score = total


@frappe.whitelist()
def get_kra(employee):
	kra_template = frappe.db.get_value("Appraisal", {"employee": employee}, "kra_template")
	return frappe.get_doc("Appraisal Template", kra_template)
