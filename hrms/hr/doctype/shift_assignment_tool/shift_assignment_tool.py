# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from datetime import timedelta

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder import Case, Interval
from frappe.query_builder.terms import SubQuery
from frappe.utils import get_link_to_form

from hrms.hr.utils import validate_bulk_tool_fields


class ShiftAssignmentTool(Document):
	@frappe.whitelist()
	def get_employees(self, advanced_filters: list | None = None) -> list:
		if not advanced_filters:
			advanced_filters = []

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

		if self.action == "Assign Shift":
			return self.get_employees_for_assigning_shift(filters)
		return self.get_shift_requests(filters)

	def get_employees_for_assigning_shift(self, filters):
		Employee = frappe.qb.DocType("Employee")
		query = frappe.qb.get_query(
			Employee,
			fields=[
				Employee.employee,
				Employee.employee_name,
				Employee.branch,
				Employee.department,
				Employee.default_shift,
			],
			filters=filters,
		).where(
			(Employee.status == "Active")
			& (Employee.date_of_joining <= self.start_date)
			& ((Employee.relieving_date >= self.start_date) | (Employee.relieving_date.isnull()))
		)
		if self.end_date:
			query = query.where(
				(Employee.relieving_date >= self.end_date) | (Employee.relieving_date.isnull())
			)
		if self.status == "Active":
			query = query.where(Employee.employee.notin(SubQuery(self.get_query_for_employees_with_shifts())))
		return query.run(as_dict=True)

	def get_shift_requests(self, filters):
		Employee = frappe.qb.DocType("Employee")
		ShiftRequest = frappe.qb.DocType("Shift Request")
		query = (
			frappe.qb.get_query(
				Employee,
				fields=[Employee.employee, Employee.employee_name],
				filters=filters,
			)
			.inner_join(ShiftRequest)
			.on(ShiftRequest.employee == Employee.name)
			.select(
				ShiftRequest.name,
				ShiftRequest.shift_type,
				ShiftRequest.from_date,
				ShiftRequest.to_date,
			)
			.where(ShiftRequest.status == "Draft")
		)

		if self.shift_type_filter:
			query = query.where(ShiftRequest.shift_type == self.shift_type_filter)
		if self.approver:
			query = query.where(ShiftRequest.approver == self.approver)
		if self.from_date:
			query = query.where((ShiftRequest.to_date >= self.from_date) | (ShiftRequest.to_date.isnull()))
		if self.to_date:
			query = query.where(ShiftRequest.from_date <= self.to_date)

		data = query.run(as_dict=True)
		for d in data:
			d.employee_name = d.employee + ": " + d.employee_name
			d.shift_request = get_link_to_form("Shift Request", d.name)

		return data

	def get_query_for_employees_with_shifts(self):
		ShiftAssignment = frappe.qb.DocType("Shift Assignment")
		query = frappe.qb.from_(ShiftAssignment)

		allow_multiple_shifts = frappe.db.get_single_value("HR Settings", "allow_multiple_shift_assignments")
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
		mandatory_fields = ["company", "shift_type", "start_date"]
		validate_bulk_tool_fields(self, mandatory_fields, employees, "start_date", "end_date")

		if len(employees) <= 30:
			return self._bulk_assign_shift(employees)

		frappe.enqueue(self._bulk_assign_shift, timeout=3000, employees=employees)
		frappe.msgprint(
			_("Creation of Shift Assignments has been queued. It may take a few minutes."),
			alert=True,
			indicator="blue",
		)

	def _bulk_assign_shift(self, employees: list):
		success, failure = [], []
		count = 0
		savepoint = "before_shift_assignment"

		for d in employees:
			try:
				frappe.db.savepoint(savepoint)
				assignment = self.create_shift_assignment(d)
			except Exception:
				frappe.db.rollback(save_point=savepoint)
				frappe.log_error(
					f"Bulk Assignment - Shift Assignment failed for employee {d}.",
					reference_doctype="Shift Assignment",
				)
				failure.append(d)
			else:
				success.append({"doc": get_link_to_form("Shift Assignment", assignment), "employee": d})

			count += 1
			frappe.publish_progress(count * 100 / len(employees), title=_("Assigning Shift..."))

		frappe.clear_messages()
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
		return assignment.name

	@frappe.whitelist()
	def bulk_process_shift_requests(self, shift_requests: list, status: str):
		if not shift_requests:
			frappe.throw(
				_("Please select at least one Shift Request to perform this action."),
				title=_("No Shift Requests Selected"),
			)

		if len(shift_requests) <= 30:
			return self._bulk_process_shift_requests(shift_requests, status)

		frappe.enqueue(
			self._bulk_process_shift_requests, timeout=3000, shift_requests=shift_requests, status=status
		)
		frappe.msgprint(
			_("Processing of Shift Requests has been queued. It may take a few minutes."),
			alert=True,
			indicator="blue",
		)

	def _bulk_process_shift_requests(self, shift_requests: list, status: str):
		success, failure = [], []
		count = 0

		for d in shift_requests:
			try:
				shift_request = frappe.get_doc("Shift Request", d["shift_request"])
				shift_request.status = status
				shift_request.save()
				shift_request.submit()

			except Exception:
				frappe.log_error(
					f"Bulk Processing - Processing failed for Shift Request {d['shift_request']}.",
					reference_doctype="Shift Request",
				)
				failure.append(d["employee"])
			else:
				success.append(
					{"doc": get_link_to_form("Shift Request", shift_request.name), "employee": d["employee"]}
				)

			count += 1
			frappe.publish_progress(count * 100 / len(shift_requests), title=_("Processing Requests..."))

		frappe.clear_messages()
		frappe.publish_realtime(
			"completed_bulk_shift_request_processing",
			message={"success": success, "failure": failure, "for_processing": True},
			doctype="Shift Assignment Tool",
			after_commit=True,
		)
