# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.terms import SubQuery
from frappe.utils import get_link_to_form, getdate

from hrms.hr.utils import validate_bulk_tool_fields


class BulkHolidayListAssignment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		branch: DF.Link | None
		company: DF.Link | None
		department: DF.Link | None
		designation: DF.Link | None
		employment_type: DF.Link | None
		from_date: DF.Date
		grade: DF.Link | None
		holiday_list: DF.Link
	# end: auto-generated types

	def validate_assignment_start_date(self):
		holiday_list_start, holiday_list_end = frappe.db.get_value(
			"Holiday List", self.holiday_list, ["from_date", "to_date"]
		)
		assignment_start_date = getdate(self.from_date)
		if (assignment_start_date < holiday_list_start) or (assignment_start_date > holiday_list_end):
			frappe.throw(_("Assignment start date cannot be outside holiday list dates"))

	@frappe.whitelist()
	def get_employees(self, advanced_filters: list) -> list:
		quick_filter_fields = [
			"company",
			"branch",
			"department",
			"designation",
			"employment_type",
			"grade",
		]
		filters = [[d, "=", self.get(d)] for d in quick_filter_fields if self.get(d)]
		filters += advanced_filters
		filters.append(["status", "=", "Active"])

		holiday_list_start, holiday_list_end = frappe.db.get_value(
			"Holiday List", self.holiday_list, ["from_date", "to_date"]
		)

		Assignment = frappe.qb.DocType("Holiday List Assignment")
		employees_with_assignments = SubQuery(
			frappe.qb.from_(Assignment)
			.select(Assignment.assigned_to)
			.distinct()
			.where(
				(Assignment.applicable_for == "Employee")
				& (Assignment.from_date[holiday_list_start:holiday_list_end])
				& (Assignment.docstatus == 1)
			)
		)

		Employee = frappe.qb.DocType("Employee")
		query = frappe.qb.get_query(
			Employee,
			fields=[Employee.employee, Employee.employee_name, Employee.department, Employee.designation],
			filters=filters,
		).where(Employee.employee.notin(employees_with_assignments))
		return query.run(as_dict=True)

	@frappe.whitelist()
	def bulk_assign_holiday_list(self, employees: list) -> None:
		mandatory_fields = ["holiday_list", "from_date"]
		validate_bulk_tool_fields(self, mandatory_fields, employees)
		self.validate_assignment_start_date()

		if len(employees) <= 30:
			return self._bulk_assign_holiday_list(employees)

		frappe.enqueue(self._bulk_assign_holiday_list, timeout=3000, employees=employees)
		frappe.msgprint(
			_("Creation of Holiday List Assignments has been queued. It may take a few minutes."),
			alert=True,
			indicator="blue",
		)

	def _bulk_assign_holiday_list(self, employees: list) -> None:
		success, failure = [], []
		count = 0
		savepoint = "before_holiday_list_assignment"

		for employee in employees:
			try:
				frappe.db.savepoint(savepoint)
				assignment = frappe.new_doc("Holiday List Assignment")
				assignment.applicable_for = "Employee"
				assignment.assigned_to = employee
				assignment.holiday_list = self.holiday_list
				assignment.from_date = self.from_date
				assignment.insert()
				assignment.submit()
			except Exception:
				frappe.db.rollback(save_point=savepoint)
				frappe.log_error(
					f"Bulk Assignment - Holiday List Assignment failed for employee {employee}.",
					reference_doctype="Holiday List Assignment",
				)
				failure.append(employee)
			else:
				success.append(
					{
						"doc": get_link_to_form("Holiday List Assignment", assignment.name),
						"employee": employee,
					}
				)

			count += 1
			frappe.publish_progress(count * 100 / len(employees), title=_("Assigning Holiday List..."))

		frappe.publish_realtime(
			"completed_bulk_holiday_list_assignment",
			message={"success": success, "failure": failure},
			doctype="Bulk Holiday List Assignment",
			after_commit=True,
		)
