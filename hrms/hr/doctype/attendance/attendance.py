# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
	add_days,
	cint,
	cstr,
	format_date,
	get_datetime,
	get_link_to_form,
	getdate,
	nowdate,
)

from hrms.hr.doctype.shift_assignment.shift_assignment import has_overlapping_timings
from hrms.hr.utils import get_holiday_dates_for_employee, validate_active_employee


class DuplicateAttendanceError(frappe.ValidationError):
	pass


class OverlappingShiftAttendanceError(frappe.ValidationError):
	pass


class Attendance(Document):
	def validate(self):
		from erpnext.controllers.status_updater import validate_status

		validate_status(self.status, ["Present", "Absent", "On Leave", "Half Day", "Work From Home"])
		validate_active_employee(self.employee)
		self.validate_attendance_date()
		self.validate_duplicate_record()
		self.validate_overlapping_shift_attendance()
		self.validate_employee_status()
		self.check_leave_record()

	def on_cancel(self):
		self.unlink_attendance_from_checkins()

	def validate_attendance_date(self):
		date_of_joining = frappe.db.get_value("Employee", self.employee, "date_of_joining")

		# leaves can be marked for future dates
		if (
			self.status != "On Leave"
			and not self.leave_application
			and getdate(self.attendance_date) > getdate(nowdate())
		):
			frappe.throw(
				_("Attendance can not be marked for future dates: {0}").format(
					frappe.bold(format_date(self.attendance_date)),
				)
			)
		elif date_of_joining and getdate(self.attendance_date) < getdate(date_of_joining):
			frappe.throw(
				_("Attendance date {0} can not be less than employee {1}'s joining date: {2}").format(
					frappe.bold(format_date(self.attendance_date)),
					frappe.bold(self.employee),
					frappe.bold(format_date(date_of_joining)),
				)
			)

	def validate_duplicate_record(self):
		duplicate = self.get_duplicate_attendance_record()

		if duplicate:
			frappe.throw(
				_("Attendance for employee {0} is already marked for the date {1}: {2}").format(
					frappe.bold(self.employee),
					frappe.bold(format_date(self.attendance_date)),
					get_link_to_form("Attendance", duplicate),
				),
				title=_("Duplicate Attendance"),
				exc=DuplicateAttendanceError,
			)

	def get_duplicate_attendance_record(self) -> str | None:
		Attendance = frappe.qb.DocType("Attendance")
		query = (
			frappe.qb.from_(Attendance)
			.select(Attendance.name)
			.where(
				(Attendance.employee == self.employee)
				& (Attendance.docstatus < 2)
				& (Attendance.attendance_date == self.attendance_date)
				& (Attendance.name != self.name)
			)
		)

		if self.shift:
			query = query.where(
				((Attendance.shift.isnull()) | (Attendance.shift == ""))
				| (
					((Attendance.shift.isnotnull()) | (Attendance.shift != "")) & (Attendance.shift == self.shift)
				)
			)

		duplicate = query.run(pluck=True)

		return duplicate[0] if duplicate else None

	def validate_overlapping_shift_attendance(self):
		attendance = self.get_overlapping_shift_attendance()

		if attendance:
			frappe.throw(
				_("Attendance for employee {0} is already marked for an overlapping shift {1}: {2}").format(
					frappe.bold(self.employee),
					frappe.bold(attendance.shift),
					get_link_to_form("Attendance", attendance.name),
				),
				title=_("Overlapping Shift Attendance"),
				exc=OverlappingShiftAttendanceError,
			)

	def get_overlapping_shift_attendance(self) -> dict:
		if not self.shift:
			return {}

		Attendance = frappe.qb.DocType("Attendance")
		same_date_attendance = (
			frappe.qb.from_(Attendance)
			.select(Attendance.name, Attendance.shift)
			.where(
				(Attendance.employee == self.employee)
				& (Attendance.docstatus < 2)
				& (Attendance.attendance_date == self.attendance_date)
				& (Attendance.shift != self.shift)
				& (Attendance.name != self.name)
			)
		).run(as_dict=True)

		if same_date_attendance and has_overlapping_timings(self.shift, same_date_attendance[0].shift):
			return same_date_attendance[0]
		return {}

	def validate_employee_status(self):
		if frappe.db.get_value("Employee", self.employee, "status") == "Inactive":
			frappe.throw(_("Cannot mark attendance for an Inactive employee {0}").format(self.employee))

	def check_leave_record(self):
		LeaveApplication = frappe.qb.DocType("Leave Application")
		leave_record = (
			frappe.qb.from_(LeaveApplication)
			.select(
				LeaveApplication.leave_type,
				LeaveApplication.half_day,
				LeaveApplication.half_day_date,
				LeaveApplication.name,
			)
			.where(
				(LeaveApplication.employee == self.employee)
				& (self.attendance_date >= LeaveApplication.from_date)
				& (self.attendance_date <= LeaveApplication.to_date)
				& (LeaveApplication.status == "Approved")
				& (LeaveApplication.docstatus == 1)
			)
		).run(as_dict=True)

		if leave_record:
			for d in leave_record:
				self.leave_type = d.leave_type
				self.leave_application = d.name
				if d.half_day_date == getdate(self.attendance_date):
					self.status = "Half Day"
					frappe.msgprint(
						_("Employee {0} on Half day on {1}").format(self.employee, format_date(self.attendance_date))
					)
				else:
					self.status = "On Leave"
					frappe.msgprint(
						_("Employee {0} is on Leave on {1}").format(self.employee, format_date(self.attendance_date))
					)

		if self.status in ("On Leave", "Half Day"):
			if not leave_record:
				frappe.msgprint(
					_("No leave record found for employee {0} on {1}").format(
						self.employee, format_date(self.attendance_date)
					),
					alert=1,
				)
		elif self.leave_type:
			self.leave_type = None
			self.leave_application = None

	def validate_employee(self):
		emp = frappe.db.sql(
			"select name from `tabEmployee` where name = %s and status = 'Active'", self.employee
		)
		if not emp:
			frappe.throw(_("Employee {0} is not active or does not exist").format(self.employee))

	def unlink_attendance_from_checkins(self):
		EmployeeCheckin = frappe.qb.DocType("Employee Checkin")
		linked_logs = (
			frappe.qb.from_(EmployeeCheckin)
			.select(EmployeeCheckin.name)
			.where(EmployeeCheckin.attendance == self.name)
			.for_update()
			.run(as_dict=True)
		)

		if linked_logs:
			(
				frappe.qb.update(EmployeeCheckin)
				.set("attendance", "")
				.where(EmployeeCheckin.attendance == self.name)
			).run()

			frappe.msgprint(
				msg=_("Unlinked Attendance record from Employee Checkins: {}").format(
					", ".join(get_link_to_form("Employee Checkin", log.name) for log in linked_logs)
				),
				title=_("Unlinked logs"),
				indicator="blue",
				is_minimizable=True,
				wide=True,
			)


@frappe.whitelist()
def get_events(start, end, filters=None):
	events = []

	employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user})

	if not employee:
		return events

	from frappe.desk.reportview import get_filters_cond

	conditions = get_filters_cond("Attendance", filters, [])
	add_attendance(events, start, end, conditions=conditions)
	return events


def add_attendance(events, start, end, conditions=None):
	query = """select name, attendance_date, status
		from `tabAttendance` where
		attendance_date between %(from_date)s and %(to_date)s
		and docstatus < 2"""
	if conditions:
		query += conditions

	for d in frappe.db.sql(query, {"from_date": start, "to_date": end}, as_dict=True):
		e = {
			"name": d.name,
			"doctype": "Attendance",
			"start": d.attendance_date,
			"end": d.attendance_date,
			"title": cstr(d.status),
			"docstatus": d.docstatus,
		}
		if e not in events:
			events.append(e)


def mark_attendance(
	employee,
	attendance_date,
	status,
	shift=None,
	leave_type=None,
	late_entry=False,
	early_exit=False,
):
	savepoint = "attendance_creation"

	try:
		frappe.db.savepoint(savepoint)
		attendance = frappe.new_doc("Attendance")
		attendance.update(
			{
				"doctype": "Attendance",
				"employee": employee,
				"attendance_date": attendance_date,
				"status": status,
				"shift": shift,
				"leave_type": leave_type,
				"late_entry": late_entry,
				"early_exit": early_exit,
			}
		)
		attendance.insert()
		attendance.submit()
	except (DuplicateAttendanceError, OverlappingShiftAttendanceError):
		frappe.db.rollback(save_point=savepoint)
		return

	return attendance.name


@frappe.whitelist()
def mark_bulk_attendance(data):
	import json

	if isinstance(data, str):
		data = json.loads(data)
	data = frappe._dict(data)
	if not data.unmarked_days:
		frappe.throw(_("Please select a date."))
		return

	for date in data.unmarked_days:
		doc_dict = {
			"doctype": "Attendance",
			"employee": data.employee,
			"attendance_date": get_datetime(date),
			"status": data.status,
		}
		attendance = frappe.get_doc(doc_dict).insert()
		attendance.submit()


@frappe.whitelist()
def get_unmarked_days(employee, from_date, to_date, exclude_holidays=0):
	joining_date, relieving_date = frappe.get_cached_value(
		"Employee", employee, ["date_of_joining", "relieving_date"]
	)

	from_date = max(getdate(from_date), joining_date or getdate(from_date))
	to_date = min(getdate(to_date), relieving_date or getdate(to_date))

	records = frappe.get_all(
		"Attendance",
		fields=["attendance_date", "employee"],
		filters=[
			["attendance_date", ">=", from_date],
			["attendance_date", "<=", to_date],
			["employee", "=", employee],
			["docstatus", "!=", 2],
		],
	)

	marked_days = [getdate(record.attendance_date) for record in records]

	if cint(exclude_holidays):
		holiday_dates = get_holiday_dates_for_employee(employee, from_date, to_date)
		holidays = [getdate(record) for record in holiday_dates]
		marked_days.extend(holidays)

	unmarked_days = []

	while from_date <= to_date:
		if from_date not in marked_days:
			unmarked_days.append(from_date)

		from_date = add_days(from_date, 1)

	return unmarked_days
