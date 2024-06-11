import frappe
from frappe import _
from frappe.utils import add_days, date_diff, get_weekday, random_string

from hrms.hr.doctype.shift_assignment.shift_assignment import ShiftAssignment
from hrms.hr.doctype.shift_assignment_tool.shift_assignment_tool import create_shift_assignment


@frappe.whitelist()
def get_values(doctype: str, name: str, fields: list) -> dict[str, str]:
	return frappe.db.get_value(doctype, name, fields, as_dict=True)


@frappe.whitelist()
def get_events(
	month_start: str, month_end: str, employee_filters: dict[str, str], shift_filters: dict[str, str]
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


@frappe.whitelist()
def delete_repeating_shift_assignment(schedule: str) -> None:
	frappe.db.delete("Shift Assignment", {"schedule": schedule})
	frappe.delete_doc("Shift Assignment Schedule", schedule)


@frappe.whitelist()
def swap_shift(
	src_shift: str, src_date: str, tgt_employee: str, tgt_date: str, tgt_shift: str | None
) -> None:
	if src_shift == tgt_shift:
		frappe.throw(_("Source and target shifts cannot be the same"))

	if tgt_shift:
		tgt_shift_doc = frappe.get_doc("Shift Assignment", tgt_shift)
		tgt_company = tgt_shift_doc.company
		break_shift(tgt_shift_doc, tgt_date)
	else:
		tgt_company = frappe.db.get_value("Employee", tgt_employee, "company")

	src_shift_doc = frappe.get_doc("Shift Assignment", src_shift)
	break_shift(src_shift_doc, src_date)
	insert_shift(
		tgt_employee, tgt_company, src_shift_doc.shift_type, tgt_date, tgt_date, src_shift_doc.status
	)

	if tgt_shift:
		insert_shift(
			src_shift_doc.employee,
			src_shift_doc.company,
			tgt_shift_doc.shift_type,
			src_date,
			src_date,
			tgt_shift_doc.status,
		)


def break_shift(assignment: str | ShiftAssignment, date: str) -> None:
	if isinstance(assignment, str):
		assignment = frappe.get_doc("Shift Assignment", assignment)

	if assignment.end_date and date_diff(assignment.end_date, date) < 0:
		frappe.throw(_("Cannot break shift after end date"))
	if date_diff(assignment.start_date, date) > 0:
		frappe.throw(_("Cannot break shift before start date"))

	employee = assignment.employee
	company = assignment.company
	shift_type = assignment.shift_type
	status = assignment.status
	end_date = assignment.end_date

	if date_diff(date, assignment.start_date) == 0:
		assignment.cancel()
		assignment.delete()
	else:
		assignment.end_date = add_days(date, -1)
		assignment.save()

	if not end_date or date_diff(end_date, date) > 0:
		create_shift_assignment(employee, company, shift_type, add_days(date, 1), end_date, status)


@frappe.whitelist()
def insert_shift(
	employee: str, company: str, shift_type: str, start_date: str, end_date: str, status: str
) -> None:
	filters = {
		"doctype": "Shift Assignment",
		"employee": employee,
		"company": company,
		"shift_type": shift_type,
		"status": status,
	}
	prev_shift = frappe.db.exists(dict({"end_date": add_days(start_date, -1)}, **filters))
	next_shift = frappe.db.exists(dict({"start_date": add_days(end_date, 1)}, **filters))

	if prev_shift:
		if next_shift:
			end_date = frappe.db.get_value("Shift Assignment", next_shift, "end_date")
			frappe.db.set_value("Shift Assignment", next_shift, "docstatus", 2)
			frappe.delete_doc("Shift Assignment", next_shift)
		frappe.db.set_value("Shift Assignment", prev_shift, "end_date", end_date)

	elif next_shift:
		frappe.db.set_value("Shift Assignment", next_shift, "start_date", start_date)

	else:
		create_shift_assignment(employee, company, shift_type, start_date, end_date, status)


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
	schedule = frappe.get_doc(
		{
			"doctype": "Shift Assignment Schedule",
			"schedule": random_string(10),
			"frequency": frequency,
			"days": [{"day": day} for day in days],
		}
	).insert()

	def create_individual_assignment(start_date, end_date):
		create_shift_assignment(employee, company, shift_type, start_date, end_date, status, schedule.name)

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
				create_individual_assignment(individual_assignment_start, date)

		elif individual_assignment_start:
			create_individual_assignment(individual_assignment_start, add_days(date, -1))
			individual_assignment_start = None

		if weekday == week_end_day and gap:
			if individual_assignment_start:
				create_individual_assignment(individual_assignment_start, date)
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
