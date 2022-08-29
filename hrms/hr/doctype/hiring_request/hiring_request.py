# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import format_duration, get_link_to_form, time_diff_in_seconds


class HiringRequest(Document):
	def validate(self):
		if self.status == "Filled" and self.completed_on:
			self.time_to_fill = time_diff_in_seconds(self.completed_on, self.posting_date)

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


@frappe.whitelist()
def get_avg_time_to_fill(company=None, department=None, designation=None):
	filters = {"status": "Filled"}
	if company:
		filters["company"] = company
	if department:
		filters["department"] = department
	if designation:
		filters["designation"] = designation

	avg_time_to_fill = frappe.db.get_all(
		"Hiring Request",
		filters=filters,
		fields=["avg(time_to_fill) as average_time"],
	)[0].average_time

	return format_duration(avg_time_to_fill) if avg_time_to_fill else 0
