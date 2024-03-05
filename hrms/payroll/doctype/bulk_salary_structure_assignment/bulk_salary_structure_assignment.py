# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.custom import ConstantColumn
from frappe.query_builder.functions import Coalesce
from frappe.query_builder.terms import SubQuery

from hrms.hr.utils import notify_bulk_action_status
from hrms.payroll.doctype.salary_structure.salary_structure import (
	create_salary_structure_assignment,
)


class BulkSalaryStructureAssignment(Document):
	@frappe.whitelist()
	def get_employees(self, advanced_filters: list) -> list:
		quick_filter_fields = [
			"company",
			"employment_type",
			"branch",
			"department",
			"designation",
			"grade",
		]
		filters = [[d, "=", self.get(d)] for d in quick_filter_fields if self.get(d)]
		filters += advanced_filters

		Assignment = frappe.qb.DocType("Salary Structure Assignment")
		employees_with_assignments = SubQuery(
			frappe.qb.from_(Assignment)
			.select(Assignment.employee)
			.distinct()
			.where((Assignment.from_date == self.from_date) & (Assignment.docstatus == 1))
		)

		Employee = frappe.qb.DocType("Employee")
		Grade = frappe.qb.DocType("Employee Grade")
		query = (
			frappe.qb.get_query(
				Employee,
				fields=[Employee.employee, Employee.employee_name, Employee.grade],
				filters=filters,
			)
			.where(
				(Employee.status == "Active")
				& (Employee.date_of_joining <= self.from_date)
				& ((Employee.relieving_date > self.from_date) | (Employee.relieving_date.isnull()))
				& (Employee.employee.notin(employees_with_assignments))
			)
			.left_join(Grade)
			.on(Employee.grade == Grade.name)
			.select(
				Coalesce(Grade.default_base_pay, 0).as_("base"),
				ConstantColumn(0).as_("variable"),
			)
		)
		return query.run(as_dict=True)

	def validate_fields(self, employees: list):
		for d in ["salary_structure", "from_date", "company"]:
			if not self.get(d):
				frappe.throw(_("{0} is required").format(self.meta.get_label(d)), title=_("Missing Field"))
		if not employees:
			frappe.throw(
				_("Please select at least one employee to assign the Salary Structure."),
				title=_("No Employees Selected"),
			)

	@frappe.whitelist()
	def bulk_assign_structure(self, employees: list) -> dict:
		self.validate_fields(employees)

		def _bulk_assign_structure():
			success, failure = [], []
			count = 0
			savepoint = "before_salary_assignment"

			for d in employees:
				try:
					frappe.db.savepoint(savepoint)
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
				except Exception:
					frappe.db.rollback(save_point=savepoint)
					frappe.log_error(
						f"Bulk Assignment - Salary Structure Assignment failed for employee {d['employee']}.",
						reference_doctype="Salary Structure Assignment",
					)
					failure.append(d["employee"])
				else:
					success.append(d["employee"])

				count += 1
				frappe.publish_progress(count * 100 / len(employees), title=_("Assigning Structure..."))

			notify_bulk_action_status("Salary Structure Assignment", failure, success)
			return {"success": success, "failure": failure}

		if len(employees) <= 20:
			return _bulk_assign_structure()

		return frappe.enqueue(_bulk_assign_structure, timeout=3000)
