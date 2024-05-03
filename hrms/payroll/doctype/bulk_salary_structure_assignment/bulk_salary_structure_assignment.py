# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.custom import ConstantColumn
from frappe.query_builder.functions import Coalesce
from frappe.query_builder.terms import SubQuery
from frappe.utils import get_link_to_form

from hrms.hr.utils import validate_bulk_tool_fields
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

	@frappe.whitelist()
	def bulk_assign_structure(self, employees: list) -> None:
		mandatory_fields = ["salary_structure", "from_date", "company"]
		validate_bulk_tool_fields(self, mandatory_fields, employees)

		if len(employees) <= 30:
			return self._bulk_assign_structure(employees)

		frappe.enqueue(self._bulk_assign_structure, timeout=3000, employees=employees)
		frappe.msgprint(
			_("Creation of Salary Structure Assignments has been queued. It may take a few minutes."),
			alert=True,
			indicator="blue",
		)

	def _bulk_assign_structure(self, employees: list) -> None:
		success, failure = [], []
		count = 0
		savepoint = "before_salary_assignment"

		for d in employees:
			try:
				frappe.db.savepoint(savepoint)
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
			except Exception:
				frappe.db.rollback(save_point=savepoint)
				frappe.log_error(
					f"Bulk Assignment - Salary Structure Assignment failed for employee {d['employee']}.",
					reference_doctype="Salary Structure Assignment",
				)
				failure.append(d["employee"])
			else:
				success.append(
					{
						"doc": get_link_to_form("Salary Structure Assignment", assignment),
						"employee": d["employee"],
					}
				)

			count += 1
			frappe.publish_progress(count * 100 / len(employees), title=_("Assigning Structure..."))

		frappe.publish_realtime(
			"completed_bulk_salary_structure_assignment",
			message={"success": success, "failure": failure},
			doctype="Bulk Salary Structure Assignment",
			after_commit=True,
		)
