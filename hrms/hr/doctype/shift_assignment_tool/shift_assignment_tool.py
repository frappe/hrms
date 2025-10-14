# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from datetime import timedelta

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder import Case, Criterion, Interval
from frappe.query_builder.terms import SubQuery
from frappe.utils import get_link_to_form

from erpnext.accounts.utils import build_qb_match_conditions

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

		if self.action == "Process Shift Requests":
			return self.get_shift_requests(filters)
		return self.get_employees_for_assigning_shift(filters)

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

		self.allow_multiple_shifts = frappe.db.get_single_value(
			"HR Settings", "allow_multiple_shift_assignments"
		)
		if self.action == "Assign Shift Schedule":
			query = query.where(
				Employee.employee.notin(SubQuery(self.get_query_for_employees_with_same_shift_schedule()))
			)
		elif self.status == "Active":
			query = query.where(Employee.employee.notin(SubQuery(self.get_query_for_employees_with_shifts())))

		query = query.where(Criterion.all(build_qb_match_conditions("Employee")))

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

		query = query.where(Criterion.all(build_qb_match_conditions("Employee")))

		data = query.run(as_dict=True)
		for d in data:
			d.employee_name = d.employee + ": " + d.employee_name
			d.shift_request = get_link_to_form("Shift Request", d.name)

		return data

	def get_query_for_employees_with_shifts(self):
		ShiftAssignment = frappe.qb.DocType("Shift Assignment")
		query = (
			frappe.qb.from_(ShiftAssignment)
			.select(ShiftAssignment.employee)
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

		if self.allow_multiple_shifts:
			query = self.get_query_checking_overlapping_shift_timings(query, ShiftAssignment, self.shift_type)

		return query

	def get_query_for_employees_with_same_shift_schedule(self):
		days = frappe.get_all("Assignment Rule Day", {"parent": self.shift_schedule}, pluck="day")

		ShiftScheduleAssignment = frappe.qb.DocType("Shift Schedule Assignment")
		ShiftSchedule = frappe.qb.DocType("Shift Schedule")
		Day = frappe.qb.DocType("Assignment Rule Day")

		query = (
			frappe.qb.from_(ShiftScheduleAssignment)
			.left_join(ShiftSchedule)
			.on(ShiftSchedule.name == ShiftScheduleAssignment.shift_schedule)
			.left_join(Day)
			.on(ShiftSchedule.name == Day.parent)
			.select(ShiftScheduleAssignment.employee)
			.distinct()
			.where((ShiftScheduleAssignment.enabled == 1) & (Day.day.isin(days)))
		)

		if self.allow_multiple_shifts:
			shift_type = frappe.db.get_value("Shift Schedule", self.shift_schedule, "shift_type")
			query = self.get_query_checking_overlapping_shift_timings(query, ShiftSchedule, shift_type)

		return query

	def get_query_checking_overlapping_shift_timings(self, query, doctype, shift_type):
		shift_start, shift_end = frappe.db.get_value("Shift Type", shift_type, ["start_time", "end_time"])
		# turn it into a 48 hour clock for easier conditioning while considering overnight shifts
		if shift_end < shift_start:
			shift_end += timedelta(hours=24)

		ShiftType = frappe.qb.DocType("Shift Type")
		end_time_case = (
			Case()
			.when(ShiftType.end_time < ShiftType.start_time, ShiftType.end_time + Interval(hours=24))
			.else_(ShiftType.end_time)
		)

		return (
			query.left_join(ShiftType)
			.on(doctype.shift_type == ShiftType.name)
			.where((end_time_case >= shift_start) & (ShiftType.start_time <= shift_end))
		)

	@frappe.whitelist()
	def bulk_assign(self, employees: list):
		if self.action == "Assign Shift":
			mandatory_fields = ["shift_type"]
			doctype = "Shift Assignments"

		elif self.action == "Assign Shift Schedule":
			mandatory_fields = ["shift_schedule"]
			doctype = "Shift Schedule Assignments"

		else:
			frappe.throw(_("Invalid Action"))

		mandatory_fields.extend(["company", "start_date"])

		validate_bulk_tool_fields(self, mandatory_fields, employees, "start_date", "end_date")

		if self.action == "Assign Shift" and len(employees) <= 30:
			return self._bulk_assign(employees)

		frappe.enqueue(self._bulk_assign, timeout=3000, employees=employees)
		frappe.msgprint(
			_("Creation of {0} has been queued. It may take a few minutes.").format(doctype),
			alert=True,
			indicator="blue",
		)

	def _bulk_assign(self, employees: list):
		success, failure = [], []
		count = 0
		savepoint = "before_assignment"
		if self.action == "Assign Shift":
			doctype = "Shift Assignment"
			event = "completed_bulk_shift_assignment"
		else:
			doctype = "Shift Schedule Assignment"
			event = "completed_bulk_shift_schedule_assignment"

		for d in employees:
			try:
				frappe.db.savepoint(savepoint)
				assignment = (
					self.create_shift_schedule_assignment(d)
					if self.action == "Assign Shift Schedule"
					else create_shift_assignment(
						d,
						self.company,
						self.shift_type,
						self.start_date,
						self.end_date,
						self.status,
						self.shift_location,
					)
				)
				if self.action == "Assign Shift Schedule":
					assignment.create_shifts(self.start_date, self.end_date)

			except Exception:
				frappe.db.rollback(save_point=savepoint)
				frappe.log_error(
					f"Bulk Assignment - {doctype} failed for employee {d}.",
					reference_doctype=doctype,
				)
				failure.append(d)
			else:
				success.append({"doc": get_link_to_form(doctype, assignment.name), "employee": d})

			count += 1
			frappe.publish_progress(count * 100 / len(employees), title=_("Creating {0}...").format(doctype))

		frappe.clear_messages()
		frappe.publish_realtime(
			event,
			message={"success": success, "failure": failure},
			doctype="Shift Assignment Tool",
			after_commit=True,
		)

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

	def create_shift_schedule_assignment(self, employee: str) -> str:
		assignment = frappe.new_doc("Shift Schedule Assignment")
		assignment.shift_schedule = self.shift_schedule
		assignment.employee = employee
		assignment.company = self.company
		assignment.shift_status = self.status
		assignment.shift_location = self.shift_location
		assignment.enabled = 0 if self.end_date else 1
		assignment.create_shifts_after = self.start_date
		assignment.flags.ingore_validate = True
		assignment.save()
		return assignment


def create_shift_assignment(
	employee: str,
	company: str,
	shift_type: str,
	start_date: str,
	end_date: str,
	status: str,
	shift_location: str | None = None,
	shift_schedule_assignment: str | None = None,
) -> str:
	assignment = frappe.new_doc("Shift Assignment")
	assignment.employee = employee
	assignment.company = company
	assignment.shift_type = shift_type
	assignment.start_date = start_date
	assignment.end_date = end_date
	assignment.status = status
	assignment.shift_location = shift_location
	assignment.shift_schedule_assignment = shift_schedule_assignment
	assignment.save()
	assignment.submit()
	return assignment
