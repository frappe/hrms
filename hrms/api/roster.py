import frappe
from frappe.utils import add_days, date_diff, get_weekday

from hrms.hr.doctype.shift_assignment_tool.shift_assignment_tool import create_shift_assignment


@frappe.whitelist()
def get_values(
	doctype: str,
	name: str,
	fields: list,
) -> dict[str, str]:
	return frappe.db.get_value(doctype, name, fields, as_dict=True)


@frappe.whitelist()
def get_events(
	month_start: str,
	month_end: str,
	employee_filters: dict[str, str],
	shift_filters: dict[str, str],
) -> dict[str, list[dict]]:
	holidays = get_holidays(month_start, month_end, employee_filters)
	leaves = get_leaves(month_start, month_end, employee_filters)
	shifts = get_shifts(month_start, month_end, employee_filters, shift_filters)

	events = {}
	for event in [holidays, leaves, shifts]:
		event = group_by_employee(event)
		for key, value in event.items():
			if key in events:
				events[key].extend(value)
			else:
				events[key] = value
	return events


@frappe.whitelist()
def create_repeating_shift_assignment(
	employee: str,
	company: str,
	shift_type: str,
	status: str,
	start_date: str,
	end_date: str,
	days: list[str],
	frequency: str,
) -> None:
	if date_diff(end_date, start_date) <= 100:
		return _create_repeating_shift_assignment(
			employee, company, shift_type, status, start_date, end_date, days, frequency
		)

	frappe.enqueue(
		_create_repeating_shift_assignment,
		timeout=4500,
		employee=employee,
		company=company,
		shift_type=shift_type,
		status=status,
		start_date=start_date,
		end_date=end_date,
		days=days,
		frequency=frequency,
	)


def _create_repeating_shift_assignment(
	employee: str,
	company: str,
	shift_type: str,
	status: str,
	start_date: str,
	end_date: str,
	days: list[str],
	frequency: str,
) -> None:
	def create_individual_assignment(start_date, end_date):
		create_shift_assignment(
			employee,
			company,
			shift_type,
			start_date,
			end_date,
			status,
		)

	gap = {
		"Every Week": 0,
		"Every 2 Weeks": 1,
		"Every 3 Weeks": 2,
		"Every 4 Weeks": 3,
	}[frequency]

	date = start_date
	individual_assignment_start = None
	week_end_day = get_weekday(add_days(start_date, -1))

	while date <= end_date:
		weekday = get_weekday(date)
		if weekday in days:
			if not individual_assignment_start:
				individual_assignment_start = date
			if date == end_date:
				create_individual_assignment(
					individual_assignment_start,
					date,
				)

		elif individual_assignment_start:
			create_individual_assignment(
				individual_assignment_start,
				add_days(date, -1),
			)
			individual_assignment_start = None

		if weekday == week_end_day and gap:
			create_individual_assignment(
				individual_assignment_start,
				date,
			)
			individual_assignment_start = None
			date = add_days(date, 7 * gap)

		date = add_days(date, 1)


def get_holidays(month_start: str, month_end: str, employee_filters: dict[str, str]) -> dict[str, list[dict]]:
	Employee = frappe.qb.DocType("Employee")
	HolidayList = frappe.qb.DocType("Holiday List")
	Holiday = frappe.qb.DocType("Holiday")

	query = (
		frappe.qb.select(
			Employee.employee,
			Holiday.name.as_("holiday"),
			Holiday.holiday_date,
			Holiday.description,
			Holiday.weekly_off,
		)
		.from_(Employee)
		.join(HolidayList)
		.on(Employee.holiday_list == HolidayList.name)
		.join(Holiday)
		.on(Holiday.parent == HolidayList.name)
		.where(Holiday.holiday_date[month_start:month_end])
	)

	for filter in employee_filters:
		query = query.where(Employee[filter] == employee_filters[filter])

	return query.run(as_dict=True)


def get_leaves(month_start: str, month_end: str, employee_filters: dict[str, str]) -> dict[str, list[dict]]:
	LeaveApplication = frappe.qb.DocType("Leave Application")
	Employee = frappe.qb.DocType("Employee")

	query = (
		frappe.qb.select(
			LeaveApplication.name.as_("leave"),
			LeaveApplication.employee,
			LeaveApplication.leave_type,
			LeaveApplication.from_date,
			LeaveApplication.to_date,
		)
		.from_(LeaveApplication)
		.left_join(Employee)
		.on(LeaveApplication.employee == Employee.name)
		.where(
			(LeaveApplication.docstatus == 1)
			& (LeaveApplication.status == "Approved")
			& (LeaveApplication.from_date <= month_end)
			& (LeaveApplication.to_date >= month_start)
		)
	)

	for filter in employee_filters:
		query = query.where(Employee[filter] == employee_filters[filter])

	return query.run(as_dict=True)


def get_shifts(
	month_start: str, month_end: str, employee_filters: dict[str, str], shift_filters: dict[str, str]
) -> dict[str, list[dict]]:
	ShiftAssignment = frappe.qb.DocType("Shift Assignment")
	ShiftType = frappe.qb.DocType("Shift Type")
	Employee = frappe.qb.DocType("Employee")

	query = (
		frappe.qb.select(
			ShiftAssignment.name,
			ShiftAssignment.employee,
			ShiftAssignment.shift_type,
			ShiftAssignment.start_date,
			ShiftAssignment.end_date,
			ShiftAssignment.status,
			ShiftType.start_time,
			ShiftType.end_time,
			ShiftType.color,
		)
		.from_(ShiftAssignment)
		.left_join(ShiftType)
		.on(ShiftAssignment.shift_type == ShiftType.name)
		.left_join(Employee)
		.on(ShiftAssignment.employee == Employee.name)
		.where(
			(ShiftAssignment.docstatus == 1)
			& (ShiftAssignment.start_date <= month_end)
			& ((ShiftAssignment.end_date >= month_start) | (ShiftAssignment.end_date.isnull()))
		)
	)

	for filter in employee_filters:
		query = query.where(Employee[filter] == employee_filters[filter])

	for filter in shift_filters:
		query = query.where(ShiftAssignment[filter] == shift_filters[filter])

	return query.run(as_dict=True)


def group_by_employee(events: list[dict]) -> dict[str, list[dict]]:
	grouped_events = {}
	for event in events:
		grouped_events.setdefault(event["employee"], []).append(
			{k: v for k, v in event.items() if k != "employee"}
		)
	return grouped_events
