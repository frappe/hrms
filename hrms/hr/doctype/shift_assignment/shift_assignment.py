# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder import Criterion
from frappe.utils import add_days, cint, cstr, get_link_to_form, get_time, getdate, now_datetime

from hrms.hr.utils import validate_active_employee
from hrms.utils import generate_date_range


class OverlappingShiftError(frappe.ValidationError):
	pass


class MultipleShiftError(frappe.ValidationError):
	pass


class ShiftAssignment(Document):
	def validate(self):
		validate_active_employee(self.employee)
		if self.end_date:
			self.validate_from_to_dates("start_date", "end_date")
		self.validate_overlapping_shifts()

	def on_update_after_submit(self):
		if self.end_date:
			self.validate_from_to_dates("start_date", "end_date")
		self.validate_overlapping_shifts()

	def on_cancel(self):
		self.validate_employee_checkin()
		self.validate_attendance()

	def validate_employee_checkin(self):
		checkins = frappe.get_all(
			"Employee Checkin",
			filters={
				"employee": self.employee,
				"shift": self.shift_type,
				"time": ["between", [self.start_date, self.end_date]],
			},
			pluck="name",
		)
		if checkins:
			frappe.throw(
				_("Cannot cancel Shift Assignment: {0} as it is linked to Employee Checkin: {1}").format(
					self.name, get_link_to_form("Employee Checkin", checkins[0])
				)
			)

	def validate_attendance(self):
		attendances = frappe.get_all(
			"Attendance",
			filters={
				"employee": self.employee,
				"shift": self.shift_type,
				"attendance_date": ["between", [self.start_date, self.end_date]],
			},
			pluck="name",
		)
		if attendances:
			frappe.throw(
				_("Cannot cancel Shift Assignment: {0} as it is linked to Attendance: {1}").format(
					self.name, get_link_to_form("Attendance", attendances[0])
				)
			)

	def validate_overlapping_shifts(self):
		if self.status == "Inactive":
			return

		overlapping_dates = self.get_overlapping_dates()
		if len(overlapping_dates):
			self.validate_same_date_multiple_shifts(overlapping_dates)
			# if dates are overlapping, check if timings are overlapping, else allow
			for d in overlapping_dates:
				if has_overlapping_timings(self.shift_type, d.shift_type):
					self.throw_overlap_error(d)

	def validate_same_date_multiple_shifts(self, overlapping_dates):
		if cint(frappe.db.get_single_value("HR Settings", "allow_multiple_shift_assignments")):
			if not self.docstatus:
				frappe.msgprint(
					_(
						"Warning: {0} already has an active Shift Assignment {1} for some/all of these dates."
					).format(
						frappe.bold(self.employee),
						get_link_to_form("Shift Assignment", overlapping_dates[0].name),
					)
				)
		else:
			msg = _("{0} already has an active Shift Assignment {1} for some/all of these dates.").format(
				frappe.bold(self.employee),
				get_link_to_form("Shift Assignment", overlapping_dates[0].name),
			)
			msg += "<br><br>"
			msg += _("To allow this, enable {0} under {1}.").format(
				frappe.bold(_("Allow Multiple Shift Assignments for Same Date")),
				get_link_to_form("HR Settings", "HR Settings"),
			)

			frappe.throw(
				title=_("Multiple Shift Assignments"),
				msg=msg,
				exc=MultipleShiftError,
			)

	def get_overlapping_dates(self):
		if not self.name:
			self.name = "New Shift Assignment"

		shift = frappe.qb.DocType("Shift Assignment")
		query = (
			frappe.qb.from_(shift)
			.select(shift.name, shift.shift_type, shift.docstatus, shift.status)
			.where(
				(shift.employee == self.employee)
				& (shift.docstatus == 1)
				& (shift.name != self.name)
				& (shift.status == "Active")
				& ((shift.end_date >= self.start_date) | (shift.end_date.isnull()))
			)
		)

		if self.end_date:
			query = query.where(shift.start_date <= self.end_date)

		return query.run(as_dict=True)

	def throw_overlap_error(self, shift_details):
		shift_details = frappe._dict(shift_details)
		if shift_details.docstatus == 1 and shift_details.status == "Active":
			msg = _(
				"Employee {0} already has an active Shift {1}: {2} that overlaps within this period."
			).format(
				frappe.bold(self.employee),
				frappe.bold(shift_details.shift_type),
				get_link_to_form("Shift Assignment", shift_details.name),
			)
			frappe.throw(msg, title=_("Overlapping Shifts"), exc=OverlappingShiftError)


def has_overlapping_timings(shift_1: str, shift_2: str) -> bool:
	"""
	Accepts two shift types and checks whether their timings are overlapping
	"""

	s1 = frappe.db.get_value("Shift Type", shift_1, ["start_time", "end_time"], as_dict=True)
	s2 = frappe.db.get_value("Shift Type", shift_2, ["start_time", "end_time"], as_dict=True)

	for d in [s1, s2]:
		if d.end_time <= d.start_time:
			d.end_time += timedelta(days=1)

	return s1.end_time > s2.start_time and s1.start_time < s2.end_time


@frappe.whitelist()
def get_events(start, end, filters=None):
	employee = frappe.db.get_value(
		"Employee", {"user_id": frappe.session.user}, ["name", "company"], as_dict=True
	)
	if employee:
		employee = employee.name
	else:
		employee = ""

	assignments = get_shift_assignments(start, end, filters)
	return get_shift_events(assignments)


def get_shift_assignments(start: str, end: str, filters: str | list | None = None) -> list[dict]:
	import json

	if isinstance(filters, str):
		filters = json.loads(filters)
	if not filters:
		filters = []

	filters.extend([["start_date", "<=", end], ["docstatus", "=", 1]])

	or_filters = [["end_date", ">=", start], ["end_date", "is", "not set"]]

	return frappe.get_list(
		"Shift Assignment",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name",
			"start_date",
			"end_date",
			"employee_name",
			"employee",
			"docstatus",
			"shift_type",
		],
	)


def get_shift_events(assignments: list[dict]) -> list[dict]:
	events = []
	shift_timing_map = get_shift_type_timing([d.shift_type for d in assignments])

	for d in assignments:
		daily_event_start = d.start_date
		daily_event_end = d.end_date or getdate()
		shift_start = shift_timing_map[d.shift_type]["start_time"]
		shift_end = shift_timing_map[d.shift_type]["end_time"]

		delta = timedelta(days=1)
		while daily_event_start <= daily_event_end:
			start_timing = frappe.utils.get_datetime(daily_event_start) + shift_start

			if shift_start > shift_end:
				# shift spans across 2 days
				end_timing = frappe.utils.get_datetime(daily_event_start) + shift_end + delta
			else:
				end_timing = frappe.utils.get_datetime(daily_event_start) + shift_end

			event = {
				"name": d.name,
				"doctype": "Shift Assignment",
				"start_date": start_timing,
				"end_date": end_timing,
				"title": cstr(d.employee_name) + ": " + cstr(d.shift_type),
				"docstatus": d.docstatus,
				"allDay": 0,
				"convertToUserTz": 0,
			}
			if event not in events:
				events.append(event)

			daily_event_start += delta

	return events


def get_shift_type_timing(shift_types):
	shift_timing_map = {}
	data = frappe.get_all(
		"Shift Type",
		filters={"name": ("IN", shift_types)},
		fields=["name", "start_time", "end_time"],
	)

	for d in data:
		shift_timing_map[d.name] = d

	return shift_timing_map


def get_shift_for_time(shifts: list[dict], for_timestamp: datetime) -> dict:
	"""Returns shift with details for given timestamp"""
	valid_shifts = []

	for assignment in shifts:
		shift_details = get_shift_details(assignment.shift_type, for_timestamp=for_timestamp)

		if _is_shift_outside_assignment_period(shift_details, assignment):
			continue

		if _is_timestamp_within_shift(shift_details, for_timestamp):
			valid_shifts.append(shift_details)

	valid_shifts.sort(key=lambda x: x["actual_start"])
	_adjust_overlapping_shifts(valid_shifts)

	return get_exact_shift(valid_shifts, for_timestamp)


def _is_shift_outside_assignment_period(shift_details: dict, assignment: dict) -> bool:
	"""
	Compares shift's actual start and end dates with assignment dates
	and returns True is shift is outside assignment period
	"""
	# start time > end time, means its a midnight shift
	is_midnight_shift = shift_details.actual_start.time() > shift_details.actual_end.time()

	if _is_shift_start_before_assignment(shift_details, assignment, is_midnight_shift):
		return True

	if assignment.end_date and _is_shift_end_after_assignment(shift_details, assignment, is_midnight_shift):
		return True

	return False


def _is_shift_start_before_assignment(shift_details: dict, assignment: dict, is_midnight_shift: bool) -> bool:
	if shift_details.actual_start.date() < assignment.start_date:
		# log's start date can only precede assignment's start date if its a midnight shift
		if not is_midnight_shift:
			return True

		# if actual start and start dates are same but it precedes assignment start date
		# then its actually a shift that starts on the previous day, making it invalid
		if shift_details.actual_start.date() == shift_details.start_datetime.date():
			return True

		# actual start is not the prev assignment day
		# then its a shift that starts even before the prev day, making it invalid
		prev_assignment_day = add_days(assignment.start_date, -1)
		if shift_details.actual_start.date() != prev_assignment_day:
			return True

	return False


def _is_shift_end_after_assignment(shift_details: dict, assignment: dict, is_midnight_shift: bool) -> bool:
	if shift_details.actual_start.date() > assignment.end_date:
		return True

	# log's end date can only exceed assignment's end date if its a midnight shift
	if shift_details.actual_end.date() > assignment.end_date:
		if not is_midnight_shift:
			return True

		# if shift starts & ends on the same day along with shift margin
		# then actual end cannot exceed assignment's end date, making it invalid
		if (
			shift_details.actual_end.date() == shift_details.end_datetime.date()
			and shift_details.start_datetime.date() == shift_details.end_datetime.date()
		):
			return True

		# actual end is not the immediate next assignment day
		# then its a shift that ends even after the next day, making it invalid
		next_assignment_day = add_days(assignment.end_date, 1)
		if shift_details.actual_end.date() != next_assignment_day:
			return True

	return False


def _is_timestamp_within_shift(shift_details: dict, for_timestamp: datetime) -> bool:
	"""Checks whether the timestamp is within shift's actual start and end datetime"""
	return shift_details.actual_start <= for_timestamp <= shift_details.actual_end


def _adjust_overlapping_shifts(shifts: dict):
	"""
	Compares 2 consecutive shifts and adjusts start and end times
	if they are overlapping within grace period
	"""
	for i in range(len(shifts) - 1):
		curr_shift = shifts[i]
		next_shift = shifts[i + 1]

		if curr_shift and next_shift:
			next_shift.actual_start = max(curr_shift.end_datetime, next_shift.actual_start)
			curr_shift.actual_end = min(next_shift.actual_start, curr_shift.actual_end)

		shifts[i] = curr_shift
		shifts[i + 1] = next_shift


def get_shifts_for_date(employee: str, for_timestamp: datetime) -> list[dict[str, str]]:
	"""Returns list of shifts with details for given date"""
	for_date = for_timestamp.date()
	prev_day = add_days(for_date, -1)
	next_day = add_days(for_date, 1)

	assignment = frappe.qb.DocType("Shift Assignment")
	return (
		frappe.qb.from_(assignment)
		.select(assignment.name, assignment.shift_type, assignment.start_date, assignment.end_date)
		.where(
			(assignment.employee == employee)
			& (assignment.docstatus == 1)
			& (assignment.status == "Active")
			# for shifts that exceed a day in duration or margins
			# eg: shift = 00:30:00 - 10:00:00, including margins (1 hr) = 23:30:00 - 11:00:00
			# if for_timestamp = 23:30:00 (falls in before shift margin), also fetch next days shift to find the correct shift
			& (assignment.start_date <= next_day)
			& (
				Criterion.any(
					[
						assignment.end_date.isnull(),
						(
							assignment.end_date.isnotnull()
							# for shifts that exceed a day in duration or margins
							# eg: shift = 15:00 - 23:30, including margins (1 hr) = 14:00 - 00:30
							# if for_timestamp = 00:30:00 (falls in after shift margin), also fetch prev days shift to find the correct shift
							& (prev_day <= assignment.end_date)
						),
					]
				)
			)
		)
	).run(as_dict=True)


def get_shift_for_timestamp(employee: str, for_timestamp: datetime) -> dict:
	shifts = get_shifts_for_date(employee, for_timestamp)
	if shifts:
		return get_shift_for_time(shifts, for_timestamp)
	return {}


def get_employee_shift(
	employee: str,
	for_timestamp: datetime | None = None,
	consider_default_shift: bool = False,
	next_shift_direction: str | None = None,
) -> dict:
	"""Returns a Shift Type for the given employee on the given date

	:param employee: Employee for which shift is required.
	:param for_timestamp: DateTime on which shift is required
	:param consider_default_shift: If set to true, default shift is taken when no shift assignment is found.
	:param next_shift_direction: One of: None, 'forward', 'reverse'. Direction to look for next shift if shift not found on given date.
	"""
	if for_timestamp is None:
		for_timestamp = now_datetime()

	shift_details = get_shift_for_timestamp(employee, for_timestamp)

	# if shift assignment is not found, consider default shift
	default_shift = frappe.db.get_value("Employee", employee, "default_shift", cache=True)
	if not shift_details and consider_default_shift:
		shift_details = get_shift_details(default_shift, for_timestamp)

	# if no shift is found, find next or prev shift assignment based on direction
	if not shift_details and next_shift_direction:
		shift_details = get_prev_or_next_shift(
			employee, for_timestamp, consider_default_shift, default_shift, next_shift_direction
		)

	return shift_details or {}


def get_prev_or_next_shift(
	employee: str,
	for_timestamp: datetime,
	consider_default_shift: bool,
	default_shift: str,
	next_shift_direction: str,
) -> dict:
	"""Returns a dict of shift details for the next or prev shift based on the next_shift_direction"""
	MAX_DAYS = 366
	shift_details = {}

	if consider_default_shift and default_shift:
		direction = -1 if next_shift_direction == "reverse" else 1
		for i in range(MAX_DAYS):
			date = for_timestamp + timedelta(days=direction * (i + 1))
			shift_details = get_employee_shift(employee, date, consider_default_shift, None)
			if shift_details:
				return shift_details
	else:
		direction = "<" if next_shift_direction == "reverse" else ">"
		sort_order = "desc" if next_shift_direction == "reverse" else "asc"
		shift_dates = frappe.get_all(
			"Shift Assignment",
			["start_date", "end_date"],
			{
				"employee": employee,
				"start_date": (direction, for_timestamp.date()),
				"docstatus": 1,
				"status": "Active",
			},
			as_list=True,
			limit=MAX_DAYS,
			order_by="start_date " + sort_order,
		)

		for date_range in shift_dates:
			# midnight shifts will span more than a day
			start_date, end_date = getdate(date_range[0]), getdate(add_days(date_range[1], 1))

			if reverse := (next_shift_direction == "reverse"):
				end_date = min(end_date, for_timestamp.date())
			elif next_shift_direction == "forward":
				start_date = max(start_date, for_timestamp.date())

			for dt in generate_date_range(start_date, end_date, reverse=reverse):
				shift_details = get_employee_shift(
					employee, datetime.combine(dt, for_timestamp.time()), consider_default_shift, None
				)
				if shift_details:
					return shift_details

	return shift_details or {}


def get_employee_shift_timings(
	employee: str, for_timestamp: datetime | None = None, consider_default_shift: bool = False
) -> list[dict]:
	"""Returns previous shift, current/upcoming shift, next_shift for the given timestamp and employee"""
	if for_timestamp is None:
		for_timestamp = now_datetime()

	# write and verify a test case for midnight shift.
	prev_shift = curr_shift = next_shift = None
	curr_shift = get_employee_shift(employee, for_timestamp, consider_default_shift, "forward")
	if curr_shift:
		next_shift = get_employee_shift(
			employee,
			curr_shift.start_datetime + timedelta(days=1),
			consider_default_shift,
			"forward",
		)
	prev_shift = get_employee_shift(
		employee,
		(curr_shift.end_datetime if curr_shift else for_timestamp) + timedelta(days=-1),
		consider_default_shift,
		"reverse",
	)

	if curr_shift:
		# adjust actual start and end times if they are overlapping with grace period (before start and after end)
		if prev_shift:
			curr_shift.actual_start = (
				prev_shift.end_datetime
				if curr_shift.actual_start < prev_shift.end_datetime
				else curr_shift.actual_start
			)
			prev_shift.actual_end = (
				curr_shift.actual_start
				if prev_shift.actual_end > curr_shift.actual_start
				else prev_shift.actual_end
			)
		if next_shift:
			next_shift.actual_start = (
				curr_shift.end_datetime
				if next_shift.actual_start < curr_shift.end_datetime
				else next_shift.actual_start
			)
			curr_shift.actual_end = (
				next_shift.actual_start
				if curr_shift.actual_end > next_shift.actual_start
				else curr_shift.actual_end
			)

	return prev_shift, curr_shift, next_shift


def get_actual_start_end_datetime_of_shift(
	employee: str, for_timestamp: datetime, consider_default_shift: bool = False
) -> dict:
	"""Returns a Dict containing shift details with actual_start and actual_end datetime values
	Here 'actual' means taking into account the "begin_check_in_before_shift_start_time" and "allow_check_out_after_shift_end_time".
	Empty Dict is returned if the timestamp is outside any actual shift timings.

	:param employee (str): Employee name
	:param for_timestamp (datetime, optional): Datetime value of checkin, if not provided considers current datetime
	:param consider_default_shift (bool, optional): Flag (defaults to False) to specify whether to consider
	default shift in employee master if no shift assignment is found
	"""
	shift_timings_as_per_timestamp = get_employee_shift_timings(
		employee, for_timestamp, consider_default_shift
	)
	return get_exact_shift(shift_timings_as_per_timestamp, for_timestamp)


def get_exact_shift(shifts: list, for_timestamp: datetime) -> dict:
	"""Returns the shift details (dict) for the exact shift in which the 'for_timestamp' value falls among multiple shifts"""

	return next(
		(
			shift
			for shift in shifts
			if shift and for_timestamp >= shift.actual_start and for_timestamp <= shift.actual_end
		),
		{},
	)


def get_shift_details(shift_type_name: str, for_timestamp: datetime | None = None) -> dict:
	"""Returns a Dict containing shift details with the following data:
	'shift_type' - Object of DocType Shift Type,
	'start_datetime' - datetime of shift start on given timestamp,
	'end_datetime' - datetime of shift end on given timestamp,
	'actual_start' - datetime of shift start after adding 'begin_check_in_before_shift_start_time',
	'actual_end' - datetime of shift end after adding 'allow_check_out_after_shift_end_time' (None is returned if this is zero)

	:param shift_type_name (str): shift type name for which shift_details are required.
	:param for_timestamp (datetime, optional): Datetime value of checkin, if not provided considers current datetime
	"""
	if not shift_type_name:
		return frappe._dict()

	if for_timestamp is None:
		for_timestamp = now_datetime()

	shift_type = get_shift_type(shift_type_name)
	start_datetime, end_datetime = get_shift_timings(shift_type, for_timestamp)

	actual_start = start_datetime - timedelta(minutes=shift_type.begin_check_in_before_shift_start_time)
	actual_end = end_datetime + timedelta(minutes=shift_type.allow_check_out_after_shift_end_time)

	return frappe._dict(
		{
			"shift_type": shift_type,
			"start_datetime": start_datetime,
			"end_datetime": end_datetime,
			"actual_start": actual_start,
			"actual_end": actual_end,
		}
	)


def get_shift_type(shift_type_name: str) -> dict:
	return frappe.get_cached_value(
		"Shift Type",
		shift_type_name,
		[
			"name",
			"start_time",
			"end_time",
			"begin_check_in_before_shift_start_time",
			"allow_check_out_after_shift_end_time",
		],
		as_dict=1,
	)


def get_shift_timings(shift_type: dict, for_timestamp: datetime) -> tuple:
	start_time = shift_type.start_time
	end_time = shift_type.end_time

	shift_actual_start = get_time(
		datetime.combine(for_timestamp, datetime.min.time())
		+ start_time
		- timedelta(minutes=shift_type.begin_check_in_before_shift_start_time)
	)
	shift_actual_end = get_time(
		datetime.combine(for_timestamp, datetime.min.time())
		+ end_time
		+ timedelta(minutes=shift_type.allow_check_out_after_shift_end_time)
	)
	for_time = get_time(for_timestamp.time())
	start_datetime = end_datetime = None

	if start_time > end_time:
		# shift spans across 2 different days
		if for_time >= shift_actual_start:
			# if for_timestamp is greater than start time, it's within the first day
			start_datetime = datetime.combine(for_timestamp, datetime.min.time()) + start_time
			for_timestamp += timedelta(days=1)
			end_datetime = datetime.combine(for_timestamp, datetime.min.time()) + end_time

		elif for_time < shift_actual_start:
			# if for_timestamp is less than start time, it's within the second day
			end_datetime = datetime.combine(for_timestamp, datetime.min.time()) + end_time
			for_timestamp += timedelta(days=-1)
			start_datetime = datetime.combine(for_timestamp, datetime.min.time()) + start_time
	elif (
		shift_actual_start > shift_actual_end
		and for_time < shift_actual_start
		and get_time(end_time) > shift_actual_end
	):
		# for_timestamp falls within the margin period in the second day (after midnight)
		# so shift started and ended on the previous day
		for_timestamp += timedelta(days=-1)
		end_datetime = datetime.combine(for_timestamp, datetime.min.time()) + end_time
		start_datetime = datetime.combine(for_timestamp, datetime.min.time()) + start_time
	elif (
		shift_actual_start > shift_actual_end
		and for_time > shift_actual_end
		and get_time(start_time) < shift_actual_start
	):
		# for_timestamp falls within the margin period in the first day (before midnight)
		# so shift started and ended on the next day
		for_timestamp += timedelta(days=1)
		start_datetime = datetime.combine(for_timestamp, datetime.min.time()) + start_time
		end_datetime = datetime.combine(for_timestamp, datetime.min.time()) + end_time
	else:
		# start and end timings fall on the same day
		start_datetime = datetime.combine(for_timestamp, datetime.min.time()) + start_time
		end_datetime = datetime.combine(for_timestamp, datetime.min.time()) + end_time

	return start_datetime, end_datetime
