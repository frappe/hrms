# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.terms import SubQuery
from frappe.utils import get_link_to_form

from hrms.hr.utils import validate_bulk_tool_fields


class BulkHolidayListAssignment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		branch: DF.Link | None
		company: DF.Link
		department: DF.Link | None
		designation: DF.Link | None
		employment_type: DF.Link | None
		from_date: DF.Date
		grade: DF.Link | None
		holiday_list: DF.Link
	# end: auto-generated types

	@frappe.whitelist()
	def get_employees(self) -> list:
		quick_filter_fields = [
			"company",
			"employment_type",
			"branch",
			"department",
			"designation",
			"grade",
		]
		filters = [[d, "=", self.get(d)] for d in quick_filter_fields if self.get(d)]

		HolidayListAssignment = frappe.qb.DocType("Holiday List Assignment")
		employees_with_assignments = SubQuery(
			frappe.qb.from_(HolidayListAssignment)
			.select(HolidayListAssignment.assigned_to)
			.distinct()
			.where(
				(HolidayListAssignment.applicable_for == "Employee")
				& (HolidayListAssignment.holiday_list == self.holiday_list)
				& (HolidayListAssignment.docstatus == 1)
			)
		)

		Employee = frappe.qb.DocType("Employee")
		query = frappe.qb.get_query(
			Employee,
			fields=[Employee.employee, Employee.employee_name, Employee.department, Employee.branch],
			filters=filters,
		).where((Employee.status == "Active") & (Employee.employee.notin(employees_with_assignments)))
		return query.run(as_dict=True)

	@frappe.whitelist()
	def bulk_assign(self, employees: list) -> None:
		mandatory_fields = ["holiday_list", "from_date", "company"]
		validate_bulk_tool_fields(self, mandatory_fields, employees)

		if len(employees) <= 30:
			return self._bulk_assign(employees)

		frappe.enqueue(self._bulk_assign, timeout=3000, employees=employees)
		frappe.msgprint(
			_("Creation of Holiday List Assignments has been queued. It may take a few minutes."),
			alert=True,
			indicator="blue",
		)

	def _bulk_assign(self, employees: list) -> None:
		success, failure = [], []
		count = 0
		savepoint = "before_holiday_assignment"

		for d in employees:
			try:
				frappe.db.savepoint(savepoint)
				assignment = frappe.new_doc("Holiday List Assignment")
				assignment.applicable_for = "Employee"
				assignment.assigned_to = d["employee"]
				assignment.holiday_list = self.holiday_list
				assignment.from_date = self.from_date
				assignment.save()
				assignment.submit()
			except Exception:
				frappe.db.rollback(save_point=savepoint)
				frappe.log_error(
					f"Bulk Assignment - Holiday List Assignment failed for employee {d['employee']}.",
					reference_doctype="Holiday List Assignment",
				)
				failure.append(d["employee"])
			else:
				success.append(
					{
						"doc": get_link_to_form("Holiday List Assignment", assignment.name),
						"employee": d["employee"],
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
