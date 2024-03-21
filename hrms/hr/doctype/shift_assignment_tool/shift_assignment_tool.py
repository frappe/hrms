# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from datetime import timedelta

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder import Case, Interval
from frappe.query_builder.terms import SubQuery


class ShiftAssignmentTool(Document):
	@frappe.whitelist()
	def get_employees(self, advanced_filters: list) -> list:
		quick_filter_fields = [
			"company",
			"branch",
			"department",
			"designation",
			"grade",
			"employment_type",
		]
		filters = [[d, "=", self.get(d)] for d in quick_filter_fields if self.get(d)]
		filters += advanced_filters

		Employee = frappe.qb.DocType("Employee")
		query = frappe.qb.get_query(
			Employee,
			fields=[Employee.employee, Employee.employee_name],
			filters=filters,
		).where(
			(Employee.status == "Active")
			& (Employee.date_of_joining <= self.start_date)
			& ((Employee.relieving_date >= self.start_date) | (Employee.relieving_date.isnull()))
			& (Employee.employee.notin(SubQuery(self.get_query_for_employees_with_shifts())))
		)
		if self.end_date:
			query = query.where(
				(Employee.relieving_date >= self.end_date) | (Employee.relieving_date.isnull())
			)
		return query.run(as_dict=True)

	def get_query_for_employees_with_shifts(self):
		ShiftAssignment = frappe.qb.DocType("Shift Assignment")
		query = frappe.qb.from_(ShiftAssignment)

		allow_multiple_shifts = frappe.db.get_single_value(
			"HR Settings", "allow_multiple_shift_assignments"
		)
		# join Shift Type if multiple shifts are allowed as we need to know shift timings only in this case
		if allow_multiple_shifts:
			ShiftType = frappe.qb.DocType("Shift Type")
			query = query.left_join(ShiftType).on(ShiftAssignment.shift_type == ShiftType.name)

		query = (
			query.select(ShiftAssignment.employee)
			.distinct()
			.where(
				(ShiftAssignment.status == "Active")
				& (ShiftAssignment.docstatus == 1)
				# check for overlapping dates
				& ((ShiftAssignment.end_date >= self.start_date) | (ShiftAssignment.end_date.isnull()))
			)
		)
		if self.end_date:
			query = query.where(ShiftAssignment.start_date <= self.end_date)

		# check for overlapping timings if multiple shifts are allowed
		if allow_multiple_shifts:
			shift_start, shift_end = frappe.db.get_value(
				"Shift Type", self.shift_type, ["start_time", "end_time"]
			)
			# turn it into a 48 hour clock for easier conditioning while considering overnight shifts
			if shift_end < shift_start:
				shift_end += timedelta(hours=24)
			end_time_case = (
				Case()
				.when(ShiftType.end_time < ShiftType.start_time, ShiftType.end_time + Interval(hours=24))
				.else_(ShiftType.end_time)
			)
			query = query.where((end_time_case >= shift_start) & (ShiftType.start_time <= shift_end))

		return query

	@frappe.whitelist()
	def bulk_assign_shift(self, employees: list):
		self.validate_fields(employees)

		if len(employees) <= 30:
			return self._bulk_assign_shift(employees)

		frappe.enqueue(self._bulk_assign_shift, timeout=3000, employees=employees)
		frappe.msgprint(
			_("Creation of Shift Assignments has been queued. It may take a few minutes."),
			alert=True,
			indicator="blue",
		)

	def validate_fields(self, employees: list):
		for d in ["company", "shift_type", "start_date"]:
			if not self.get(d):
				frappe.throw(_("{0} is required").format(self.meta.get_label(d)), title=_("Missing Field"))
		if self.end_date:
			self.validate_from_to_dates("start_date", "end_date")
		if not employees:
			frappe.throw(
				_("Please select at least one employee to assign the Shift."),
				title=_("No Employees Selected"),
			)

	def _bulk_assign_shift(self, employees: list):
		success, failure = [], []
		count = 0
		savepoint = "before_shift_assignment"

		for d in employees:
			try:
				frappe.db.savepoint(savepoint)
				self.create_shift_assignment(d)
			except Exception:
				frappe.db.rollback(save_point=savepoint)
				frappe.log_error(
					f"Bulk Assignment - Shift Assignment failed for employee {d}.",
					reference_doctype="Shift Assignment",
				)
				failure.append(d)
			else:
				success.append(d)

			count += 1
			frappe.publish_progress(count * 100 / len(employees), title=_("Assigning Shift..."))

		frappe.publish_realtime(
			"completed_bulk_shift_assignment",
			message={"success": success, "failure": failure},
			doctype="Shift Assignment Tool",
			after_commit=True,
		)

	def create_shift_assignment(self, employee: str):
		assignment = frappe.new_doc("Shift Assignment")
		assignment.employee = employee
		assignment.company = self.company
		assignment.shift_type = self.shift_type
		assignment.start_date = self.start_date
		assignment.end_date = self.end_date
		assignment.status = self.status
		assignment.save()
		assignment.submit()
