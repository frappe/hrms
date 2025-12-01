# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import format_duration, get_link_to_form, time_diff_in_seconds


class JobRequisition(Document):
	def validate(self):
		self.validate_duplicates()
		self.set_time_to_fill()

	def validate_duplicates(self):
		duplicate = frappe.db.exists(
			"Job Requisition",
			{
				"designation": self.designation,
				"department": self.department,
				"requested_by": self.requested_by,
				"status": ("not in", ["Cancelled", "Filled"]),
				"name": ("!=", self.name),
			},
		)

		if duplicate:
			frappe.throw(
				_("A Job Requisition for {0} requested by {1} already exists: {2}").format(
					frappe.bold(self.designation),
					frappe.bold(self.requested_by),
					get_link_to_form("Job Requisition", duplicate),
				),
				title=_("Duplicate Job Requisition"),
			)

	def set_time_to_fill(self):
		if self.status == "Filled" and self.completed_on:
			self.time_to_fill = time_diff_in_seconds(self.completed_on, self.posting_date)

	@frappe.whitelist()
	def associate_job_opening(self, job_opening):
		frappe.db.set_value(
			"Job Opening", job_opening, {"job_requisition": self.name, "vacancies": self.no_of_positions}
		)
		frappe.msgprint(
			_("Job Requisition {0} has been associated with Job Opening {1}").format(
				frappe.bold(self.name), get_link_to_form("Job Opening", job_opening)
			),
			title=_("Job Opening Associated"),
		)


@frappe.whitelist()
def make_job_opening(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.job_title = source.designation
		target.status = "Open"
		target.currency = frappe.db.get_value("Company", source.company, "default_currency")
		target.lower_range = source.expected_compensation
		target.description = source.description

	return get_mapped_doc(
		"Job Requisition",
		source_name,
		{
			"Job Requisition": {
				"doctype": "Job Opening",
			},
			"field_map": {
				"designation": "designation",
				"name": "job_requisition",
				"department": "department",
				"no_of_positions": "vacancies",
			},
		},
		target_doc,
		set_missing_values,
	)


@frappe.whitelist()
def get_avg_time_to_fill(
	company: str | None = None, department: str | None = None, designation: str | None = None
):
	filters = {"status": "Filled"}
	if company:
		filters["company"] = company
	if department:
		filters["department"] = department
	if designation:
		filters["designation"] = designation

	avg_time_to_fill = frappe.db.get_list(
		"Job Requisition",
		filters=filters,
		fields=[{"AVG": "time_to_fill", "as": "average_time"}],
	)[0].average_time

	return format_duration(avg_time_to_fill) if avg_time_to_fill else 0
