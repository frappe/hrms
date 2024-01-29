# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.query_builder.terms import SubQuery


class BulkSalaryStructureAssignment(Document):
	@frappe.whitelist()
	def get_employees(self, advanced_filters: list) -> list:
		Assignment = frappe.qb.DocType("Salary Structure Assignment")
		employees_with_assignments = (
			frappe.qb.from_(Assignment)
			.select(Assignment.employee)
			.distinct()
			.where((Assignment.from_date == self.from_date) & (Assignment.docstatus == 1))
			.run(pluck=True)
		)

		quick_filter_fields = [
			"company",
			"employment_type",
			"branch",
			"department",
			"designation",
			"grade",
		]
		quick_filters = [[d, "=", self.get(d)] for d in quick_filter_fields if self.get(d)]

		filters = (
			[["status", "=", "Active"], ["employee", "not in", employees_with_assignments]]
			+ quick_filters
			+ advanced_filters
		)
		return frappe.get_list(
			"Employee",
			filters=filters,
			fields=["employee", "employee_name", "company", "department"],
		)
