# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from hrms.payroll.doctype.salary_structure.salary_structure import (
	create_salary_structure_assignment,
)


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
			fields=["employee", "employee_name"],
		)

	def validate_fields(self, employees: list):
		for d in ["salary_structure", "from_date", "company"]:
			if not self.get(d):
				frappe.throw(_("{0} is required").format(self.meta.get_label(d)), title=_("Missing Field"))
		if not employees:
			frappe.throw(
				_("Please select the employees to whom the salary structure should be assigned"),
				title=_("No Employees Selected"),
			)

	@frappe.whitelist()
	def bulk_assign_structure(self, employees: list):
		self.validate_fields(employees)

		def _bulk_assign_structure():
			success, failure = [], []
			count = 0
			for d in employees:
				savepoint = "before_allocation_submission"
				frappe.db.savepoint(savepoint)
				try:
					create_salary_structure_assignment(
						employee=d["employee"],
						salary_structure=self.salary_structure,
						company=self.company,
						currency=self.currency,
						payroll_payable_account=self.payroll_payable_account,
						from_date=self.from_date,
						base=d["base"],
						variable=d["variable"],
						income_tax_slab=self.income_tax_slab,
					)
					success.append(d["employee"])
					count += 1
					frappe.publish_progress(count * 100 / len(employees), title=_("Assigning Structure..."))

				except Exception:
					frappe.db.rollback(save_point=savepoint)
					failure.append(d["employee"])

			return {"success": success, "failure": failure}

		if len(employees) <= 20:
			return _bulk_assign_structure()

		return frappe.enqueue(_bulk_assign_structure, timeout=600)
