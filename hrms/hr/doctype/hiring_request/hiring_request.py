# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import get_link_to_form


class HiringRequest(Document):
	@frappe.whitelist()
	def associate_job_opening(self, job_opening):
		frappe.db.set_value(
			"Job Opening", job_opening, {"hiring_request": self.name, "vacancies": self.no_of_positions}
		)
		frappe.msgprint(
			_("Hiring Request {0} is associated with Job Opening {1}").format(
				self.name, get_link_to_form("Job Opening", job_opening)
			)
		)


@frappe.whitelist()
def make_job_opening(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.job_title = source.designation
		target.status = "Open"
		target.currency = frappe.db.get_value("Company", source.company, "default_currency")
		target.lower_range = source.expected_compensation

	return get_mapped_doc(
		"Hiring Request",
		source_name,
		{
			"Hiring Request": {
				"doctype": "Job Opening",
			},
			"field_map": {
				"designation": "designation",
				"name": "hiring_request",
				"department": "department",
				"no_of_positions": "vacancies",
			},
		},
		target_doc,
		set_missing_values,
	)
