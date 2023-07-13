# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import itertools
from datetime import datetime, timedelta

import frappe
from frappe.model.document import Document
from frappe.utils import cint, get_datetime, get_time, getdate

from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
from erpnext.setup.doctype.holiday_list.holiday_list import is_holiday

from hrms.hr.doctype.attendance.attendance import mark_attendance
from hrms.hr.doctype.employee_checkin.employee_checkin import (
	calculate_working_hours,
	mark_attendance_and_link_log,
)
from hrms.hr.doctype.shift_assignment.shift_assignment import get_employee_shift, get_shift_details
from hrms.utils import get_date_range
from hrms.utils.holiday_list import get_holiday_dates_between


class ShiftType(Document):
	@frappe.whitelist()
	def process_auto_attendance(self):
		if (
			not cint(self.enable_auto_attendance)
			or not self.process_attendance_after
			or not self.last_sync_of_checkin
		):
			return

		logs = self.get_employee_checkins()

		for key, group in itertools.groupby(logs, key=lambda x: (x["employee"], x["shift_start"])):
			single_shift_logs = list(group)
			attendance_date = single_shift_logs[0].shift_actual_start.date()
			employee = key[0]

			if not self.should_mark_attendance(employee, attendance_date):
				continue

			(
				attendance_status,
				working_hours,
				late_entry,
				early_exit,
				in_time,
				out_time,
			) = self.get_attendance(single_shift_logs)

			mark_attendance_and_link_log(
				single_shift_logs,
				attendance_status,
				attendance_date,
				working_hours,
				late_entry,
				early_exit,
				in_time,
				out_time,
				self.name,
			)

		for employee in self.get_assigned_employees(self.process_attendance_after, True):
			self.mark_absent_for_dates_with_no_attendance(employee)

	def get_employee_checkins(self) -> list[dict]:
		return frappe.get_all(
			"Employee Checkin",
			fields=[
				"name",
				"employee",
				"log_type",
				"time",
				"shift",
				"shift_start",
				"shift_end",
				"shift_actual_start",
				"shift_actual_end",
				"device_id",
			],
			filters={
				"skip_auto_attendance": 0,
				"attendance": ("is", "not set"),
				"time": (">=", self.process_attendance_after),
				"shift_actual_end": ("<", self.last_sync_of_checkin),
				"shift": self.name,
			},
			order_by="employee,time",
		)

	def get_attendance(self, logs):
		"""Return attendance_status, working_hours, late_entry, early_exit, in_time, out_time
		for a set of logs belonging to a single shift.
		Assumptions:
		1. These logs belongs to a single shift, single employee and it's not in a holiday date.
		2. Logs are in chronological order
		"""
		late_entry = early_exit = False
		total_working_hours, in_time, out_time = calculate_working_hours(
			logs, self.determine_check_in_and_check_out, self.working_hours_calculation_based_on
		)
		if (
			cint(self.enable_entry_grace_period)
			and in_time
			and in_time > logs[0].shift_start + timedelta(minutes=cint(self.late_entry_grace_period))
		):
			late_entry = True

		if (
			cint(self.enable_exit_grace_period)
			and out_time
			and out_time < logs[0].shift_end - timedelta(minutes=cint(self.early_exit_grace_period))
		):
			early_exit = True

		if (
			self.working_hours_threshold_for_absent
			and total_working_hours < self.working_hours_threshold_for_absent
		):
			return "Absent", total_working_hours, late_entry, early_exit, in_time, out_time

		if (
			self.working_hours_threshold_for_half_day
			and total_working_hours < self.working_hours_threshold_for_half_day
		):
			return "Half Day", total_working_hours, late_entry, early_exit, in_time, out_time

		return "Present", total_working_hours, late_entry, early_exit, in_time, out_time

	def mark_absent_for_dates_with_no_attendance(self, employee: str):
		"""Marks Absents for the given employee on working days in this shift that have no attendance marked.
		The Absent status is marked starting from 'process_attendance_after' or employee creation date.
		"""
		start_time = get_time(self.start_time)
		dates = self.get_dates_for_attendance(employee)

		for date in dates:
			timestamp = datetime.combine(date, start_time)
			shift_details = get_employee_shift(employee, timestamp, True)

			if shift_details and shift_details.shift_type.name == self.name:
				attendance = mark_attendance(employee, date, "Absent", self.name)

				if not attendance:
					continue

				frappe.get_doc(
					{
						"doctype": "Comment",
						"comment_type": "Comment",
						"reference_doctype": "Attendance",
						"reference_name": attendance,
						"content": frappe._("Employee was marked Absent due to missing Employee Checkins."),
					}
				).insert(ignore_permissions=True)

	def get_dates_for_attendance(self, employee: str) -> set[str]:
		start_date, end_date = self.get_start_and_end_dates(employee)

		# no shift assignment found, no need to process absent attendance records
		if start_date is None:
			return set()

		date_range = get_date_range(start_date, end_date)

		# skip marking absent on holidays
		holiday_list = self.get_holiday_list(employee)
		holiday_dates = get_holiday_dates_between(holiday_list, start_date, end_date)
		# skip dates with attendance
		marked_attendance_dates = self.get_marked_attendance_dates_between(
			employee, start_date, end_date
		)

		return set(date_range) - set(holiday_dates) - set(marked_attendance_dates)

	def get_start_and_end_dates(self, employee):
		"""Returns start and end dates for checking attendance and marking absent
		return: start date = max of `process_attendance_after` and DOJ
		return: end date = min of shift before `last_sync_of_checkin` and Relieving Date
		"""
		date_of_joining, relieving_date, employee_creation = frappe.get_cached_value(
			"Employee", employee, ["date_of_joining", "relieving_date", "creation"]
		)

		if not date_of_joining:
			date_of_joining = employee_creation.date()

		start_date = max(getdate(self.process_attendance_after), date_of_joining)
		end_date = None

		shift_details = get_shift_details(self.name, get_datetime(self.last_sync_of_checkin))
		last_shift_time = (
			shift_details.actual_start if shift_details else get_datetime(self.last_sync_of_checkin)
		)

		# check if shift is found for 1 day before the last sync of checkin
		# absentees are auto-marked 1 day after the shift to wait for any manual attendance records
		prev_shift = get_employee_shift(employee, last_shift_time - timedelta(days=1), True, "reverse")
		if prev_shift:
			end_date = (
				min(prev_shift.start_datetime.date(), relieving_date)
				if relieving_date
				else prev_shift.start_datetime.date()
			)
		else:
			# no shift found
			return None, None
		return start_date, end_date

	def get_marked_attendance_dates_between(
		self, employee: str, start_date: str, end_date: str
	) -> list[str]:
		Attendance = frappe.qb.DocType("Attendance")
		return (
			frappe.qb.from_(Attendance)
			.select(Attendance.attendance_date)
			.where(
				(Attendance.employee == employee)
				& (Attendance.docstatus < 2)
				& (Attendance.attendance_date.between(start_date, end_date))
				& ((Attendance.shift.isnull()) | (Attendance.shift == self.name))
			)
		).run(pluck=True)

	def get_assigned_employees(self, from_date=None, consider_default_shift=False):
		filters = {"shift_type": self.name, "docstatus": "1", "status": "Active"}
		if from_date:
			filters["start_date"] = (">=", from_date)

		assigned_employees = frappe.get_all("Shift Assignment", filters=filters, pluck="employee")

		if consider_default_shift:
			default_shift_employees = self.get_employees_with_default_shift(filters)
			assigned_employees = set(assigned_employees + default_shift_employees)

		# exclude inactive employees
		inactive_employees = frappe.db.get_all("Employee", {"status": "Inactive"}, pluck="name")

		return set(assigned_employees) - set(inactive_employees)

	def get_employees_with_default_shift(self, filters: dict) -> list:
		default_shift_employees = frappe.get_all(
			"Employee", filters={"default_shift": self.name, "status": "Active"}, pluck="name"
		)

		if not default_shift_employees:
			return []

		# exclude employees from default shift list if any other valid shift assignment exists
		del filters["shift_type"]
		filters["employee"] = ("in", default_shift_employees)

		active_shift_assignments = frappe.get_all(
			"Shift Assignment",
			filters=filters,
			pluck="employee",
		)

		return list(set(default_shift_employees) - set(active_shift_assignments))

	def get_holiday_list(self, employee: str) -> str:
		holiday_list_name = self.holiday_list or get_holiday_list_for_employee(employee, False)
		return holiday_list_name

	def should_mark_attendance(self, employee: str, attendance_date: str) -> bool:
		"""Determines whether attendance should be marked on holidays or not"""
		if self.mark_auto_attendance_on_holidays:
			# no need to check if date is a holiday or not
			# since attendance should be marked on all days
			return True

		holiday_list = self.get_holiday_list(employee)
		if is_holiday(holiday_list, attendance_date):
			return False
		return True


def process_auto_attendance_for_all_shifts():
	shift_list = frappe.get_all("Shift Type", filters={"enable_auto_attendance": "1"}, pluck="name")
	for shift in shift_list:
		doc = frappe.get_cached_doc("Shift Type", shift)
		doc.process_auto_attendance()
