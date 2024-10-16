# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, get_datetime

from hrms.hr.doctype.shift_assignment.shift_assignment import get_actual_start_end_datetime_of_shift
from hrms.hr.utils import (
	get_distance_between_coordinates,
	set_geolocation_from_coordinates,
	validate_active_employee,
)


class CheckinRadiusExceededError(frappe.ValidationError):
	pass


class EmployeeCheckin(Document):
	def validate(self):
		validate_active_employee(self.employee)
		self.validate_duplicate_log()
		self.fetch_shift()
		set_geolocation_from_coordinates(self)
		self.validate_distance_from_shift_location()

	def validate_duplicate_log(self):
		doc = frappe.db.exists(
			"Employee Checkin",
			{
				"employee": self.employee,
				"time": self.time,
				"name": ("!=", self.name),
				"log_type": self.log_type,
			},
		)
		if doc:
			doc_link = frappe.get_desk_link("Employee Checkin", doc)
			frappe.throw(
				_("This employee already has a log with the same timestamp.{0}").format("<Br>" + doc_link)
			)

	@frappe.whitelist()
	def fetch_shift(self):
		if not (
			shift_actual_timings := get_actual_start_end_datetime_of_shift(
				self.employee, get_datetime(self.time), True
			)
		):
			self.shift = None
			return

		if (
			shift_actual_timings.shift_type.determine_check_in_and_check_out
			== "Strictly based on Log Type in Employee Checkin"
			and not self.log_type
			and not self.skip_auto_attendance
		):
			frappe.throw(
				_("Log Type is required for check-ins falling in the shift: {0}.").format(
					shift_actual_timings.shift_type.name
				)
			)
		if not self.attendance:
			self.shift = shift_actual_timings.shift_type.name
			self.shift_actual_start = shift_actual_timings.actual_start
			self.shift_actual_end = shift_actual_timings.actual_end
			self.shift_start = shift_actual_timings.start_datetime
			self.shift_end = shift_actual_timings.end_datetime

	def validate_distance_from_shift_location(self):
		if not frappe.db.get_single_value("HR Settings", "allow_geolocation_tracking"):
			return

		if not (self.latitude or self.longitude):
			frappe.throw(_("Latitude and longitude values are required for checking in."))

		assignment_locations = frappe.get_all(
			"Shift Assignment",
			filters={
				"employee": self.employee,
				"shift_type": self.shift,
				"start_date": ["<=", self.time],
				"shift_location": ["is", "set"],
				"docstatus": 1,
			},
			or_filters=[["end_date", ">=", self.time], ["end_date", "is", "not set"]],
			pluck="shift_location",
		)
		if not assignment_locations:
			return

		checkin_radius, latitude, longitude = frappe.db.get_value(
			"Shift Location", assignment_locations[0], ["checkin_radius", "latitude", "longitude"]
		)
		if checkin_radius <= 0:
			return

		distance = get_distance_between_coordinates(latitude, longitude, self.latitude, self.longitude)
		if distance > checkin_radius:
			frappe.throw(
				_("You must be within {0} meters of your shift location to check in.").format(checkin_radius),
				exc=CheckinRadiusExceededError,
			)


@frappe.whitelist()
def add_log_based_on_employee_field(
	employee_field_value,
	timestamp,
	device_id=None,
	log_type=None,
	skip_auto_attendance=0,
	employee_fieldname="attendance_device_id",
):
	"""Finds the relevant Employee using the employee field value and creates a Employee Checkin.

	:param employee_field_value: The value to look for in employee field.
	:param timestamp: The timestamp of the Log. Currently expected in the following format as string: '2019-05-08 10:48:08.000000'
	:param device_id: (optional)Location / Device ID. A short string is expected.
	:param log_type: (optional)Direction of the Punch if available (IN/OUT).
	:param skip_auto_attendance: (optional)Skip auto attendance field will be set for this log(0/1).
	:param employee_fieldname: (Default: attendance_device_id)Name of the field in Employee DocType based on which employee lookup will happen.
	"""

	if not employee_field_value or not timestamp:
		frappe.throw(_("'employee_field_value' and 'timestamp' are required."))

	employee = frappe.db.get_values(
		"Employee",
		{employee_fieldname: employee_field_value},
		["name", "employee_name", employee_fieldname],
		as_dict=True,
	)
	if employee:
		employee = employee[0]
	else:
		frappe.throw(
			_("No Employee found for the given employee field value. '{}': {}").format(
				employee_fieldname, employee_field_value
			)
		)

	doc = frappe.new_doc("Employee Checkin")
	doc.employee = employee.name
	doc.employee_name = employee.employee_name
	doc.time = timestamp
	doc.device_id = device_id
	doc.log_type = log_type
	if cint(skip_auto_attendance) == 1:
		doc.skip_auto_attendance = "1"
	doc.insert()

	return doc


@frappe.whitelist()
def bulk_fetch_shift(checkins: list[str] | str) -> None:
	if isinstance(checkins, str):
		checkins = frappe.json.loads(checkins)
	for d in checkins:
		doc = frappe.get_doc("Employee Checkin", d)
		doc.fetch_shift()
		doc.flags.ignore_validate = True
		doc.save()


def mark_attendance_and_link_log(
	logs,
	attendance_status,
	attendance_date,
	working_hours=None,
	late_entry=False,
	early_exit=False,
	in_time=None,
	out_time=None,
	shift=None,
):
	"""Creates an attendance and links the attendance to the Employee Checkin.
	Note: If attendance is already present for the given date, the logs are marked as skipped and no exception is thrown.

	:param logs: The List of 'Employee Checkin'.
	:param attendance_status: Attendance status to be marked. One of: (Present, Absent, Half Day, Skip). Note: 'On Leave' is not supported by this function.
	:param attendance_date: Date of the attendance to be created.
	:param working_hours: (optional)Number of working hours for the given date.
	"""
	log_names = [x.name for x in logs]
	employee = logs[0].employee

	if attendance_status == "Skip":
		skip_attendance_in_checkins(log_names)
		return None

	elif attendance_status in ("Present", "Absent", "Half Day"):
		try:
			frappe.db.savepoint("attendance_creation")
			attendance = frappe.new_doc("Attendance")
			attendance.update(
				{
					"doctype": "Attendance",
					"employee": employee,
					"attendance_date": attendance_date,
					"status": attendance_status,
					"working_hours": working_hours,
					"shift": shift,
					"late_entry": late_entry,
					"early_exit": early_exit,
					"in_time": in_time,
					"out_time": out_time,
				}
			).submit()

			if attendance_status == "Absent":
				attendance.add_comment(
					text=_("Employee was marked Absent for not meeting the working hours threshold.")
				)

			update_attendance_in_checkins(log_names, attendance.name)
			return attendance

		except frappe.ValidationError as e:
			handle_attendance_exception(log_names, e)

	else:
		frappe.throw(_("{} is an invalid Attendance Status.").format(attendance_status))


def calculate_working_hours(logs, check_in_out_type, working_hours_calc_type):
	"""Given a set of logs in chronological order calculates the total working hours based on the parameters.
	Zero is returned for all invalid cases.

	:param logs: The List of 'Employee Checkin'.
	:param check_in_out_type: One of: 'Alternating entries as IN and OUT during the same shift', 'Strictly based on Log Type in Employee Checkin'
	:param working_hours_calc_type: One of: 'First Check-in and Last Check-out', 'Every Valid Check-in and Check-out'
	"""
	total_hours = 0
	in_time = out_time = None
	if check_in_out_type == "Alternating entries as IN and OUT during the same shift":
		in_time = logs[0].time
		if len(logs) >= 2:
			out_time = logs[-1].time
		if working_hours_calc_type == "First Check-in and Last Check-out":
			# assumption in this case: First log always taken as IN, Last log always taken as OUT
			total_hours = time_diff_in_hours(in_time, logs[-1].time)
		elif working_hours_calc_type == "Every Valid Check-in and Check-out":
			logs = logs[:]
			while len(logs) >= 2:
				total_hours += time_diff_in_hours(logs[0].time, logs[1].time)
				del logs[:2]

	elif check_in_out_type == "Strictly based on Log Type in Employee Checkin":
		if working_hours_calc_type == "First Check-in and Last Check-out":
			first_in_log_index = find_index_in_dict(logs, "log_type", "IN")
			first_in_log = logs[first_in_log_index] if first_in_log_index or first_in_log_index == 0 else None
			last_out_log_index = find_index_in_dict(reversed(logs), "log_type", "OUT")
			last_out_log = (
				logs[len(logs) - 1 - last_out_log_index]
				if last_out_log_index or last_out_log_index == 0
				else None
			)
			in_time = getattr(first_in_log, "time", None)
			out_time = getattr(last_out_log, "time", None)
			if first_in_log and last_out_log:
				total_hours = time_diff_in_hours(in_time, out_time)
		elif working_hours_calc_type == "Every Valid Check-in and Check-out":
			in_log = out_log = None
			for log in logs:
				if in_log and out_log:
					if not in_time:
						in_time = in_log.time
					out_time = out_log.time
					total_hours += time_diff_in_hours(in_log.time, out_log.time)
					in_log = out_log = None
				if not in_log:
					in_log = log if log.log_type == "IN" else None
					if in_log and not in_time:
						in_time = in_log.time
				elif not out_log:
					out_log = log if log.log_type == "OUT" else None

			if in_log and out_log:
				out_time = out_log.time
				total_hours += time_diff_in_hours(in_log.time, out_log.time)

	return total_hours, in_time, out_time


def time_diff_in_hours(start, end):
	return round(float((end - start).total_seconds()) / 3600, 2)


def find_index_in_dict(dict_list, key, value):
	return next((index for (index, d) in enumerate(dict_list) if d[key] == value), None)


def handle_attendance_exception(log_names: list, error_message: str):
	frappe.db.rollback(save_point="attendance_creation")
	frappe.clear_messages()
	skip_attendance_in_checkins(log_names)
	add_comment_in_checkins(log_names, error_message)


def add_comment_in_checkins(log_names: list, error_message: str):
	text = "{prefix}<br>{error_message}".format(
		prefix=frappe.bold(_("Reason for skipping auto attendance:")), error_message=error_message
	)

	for name in log_names:
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Comment",
				"reference_doctype": "Employee Checkin",
				"reference_name": name,
				"content": text,
			}
		).insert(ignore_permissions=True)


def skip_attendance_in_checkins(log_names: list):
	EmployeeCheckin = frappe.qb.DocType("Employee Checkin")
	(
		frappe.qb.update(EmployeeCheckin)
		.set("skip_auto_attendance", 1)
		.where(EmployeeCheckin.name.isin(log_names))
	).run()


def update_attendance_in_checkins(log_names: list, attendance_id: str):
	EmployeeCheckin = frappe.qb.DocType("Employee Checkin")
	(
		frappe.qb.update(EmployeeCheckin)
		.set("attendance", attendance_id)
		.where(EmployeeCheckin.name.isin(log_names))
	).run()
