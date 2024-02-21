# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from pypika import functions as fn

import frappe
from frappe import _
from frappe.model.document import Document

from hrms.hr.utils import notify_status
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

		Employee = frappe.qb.DocType("Employee")
		Grade = frappe.qb.DocType("Employee Grade")
		query = (
			frappe.qb.get_query(
				Employee, fields=[Employee.employee, Employee.employee_name], filters=filters
			)
			.left_join(Grade)
			.on(Employee.grade == Grade.name)
			.select(
				fn.Coalesce(Grade.default_base_pay, 0).as_("base"),
				fn.Coalesce(0).as_("variable"),
			)
		)
		return query.run(as_dict=True)

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
	def bulk_assign_structure(self, employees: list) -> dict:
		self.validate_fields(employees)

		def _bulk_assign_structure():
			success, failure = [], []
			count = 0
			savepoint = "before_assignments_submission"
			frappe.db.savepoint(savepoint)

			for d in employees:
				assignment = create_salary_structure_assignment(
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
				if not assignment:
					frappe.db.rollback(save_point=savepoint)
					failure.append(d["employee"])
					continue

				success.append(d["employee"])
				count += 1
				frappe.publish_progress(count * 100 / len(employees), title=_("Assigning Structure..."))

			notify_status("Salary Structure Assignment", failure, success)
			return {"success": success, "failure": failure}

		if len(employees) <= 20:
			return _bulk_assign_structure()

		return frappe.enqueue(_bulk_assign_structure, timeout=600)
