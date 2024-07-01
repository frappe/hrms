import frappe
from frappe import _
from frappe.utils import add_days, date_diff

from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee

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
		for key, value in event.items():
			if key in events:
				events[key].extend(value)
			else:
				events[key] = value
	return events


@frappe.whitelist()
def create_shift_assignment_schedule(
	employee: str,
	company: str,
	shift_type: str,
	status: str,
	start_date: str,
	end_date: str | None,
	repeat_on_days: list[str],
	frequency: str,
) -> None:
	schedule = frappe.get_doc(
		{
			"doctype": "Shift Assignment Schedule",
			"frequency": frequency,
			"repeat_on_days": [{"day": day} for day in repeat_on_days],
			"enabled": 0 if end_date else 1,
			"employee": employee,
			"company": company,
			"shift_type": shift_type,
			"shift_status": status,
		}
	).insert()

	if not end_date or date_diff(end_date, start_date) <= 90:
		return schedule.create_shifts(start_date, end_date)

	frappe.enqueue(schedule.create_shifts, timeout=4500, start_date=start_date, end_date=end_date)


@frappe.whitelist()
def delete_shift_assignment_schedule(schedule: str) -> None:
	for shift_assignment in frappe.get_all("Shift Assignment", {"schedule": schedule}, pluck="name"):
		doc = frappe.get_doc("Shift Assignment", shift_assignment)
		if doc.docstatus == 1:
			doc.cancel()
		frappe.delete_doc("Shift Assignment", shift_assignment)
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


@frappe.whitelist()
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
	employee: str, company: str, shift_type: str, start_date: str, end_date: str | None, status: str
) -> None:
	filters = {
		"doctype": "Shift Assignment",
		"employee": employee,
		"company": company,
		"shift_type": shift_type,
		"status": status,
	}
	prev_shift = frappe.db.exists(dict({"end_date": add_days(start_date, -1)}, **filters))
	next_shift = (
		frappe.db.exists(dict({"start_date": add_days(end_date, 1)}, **filters)) if end_date else None
	)

	if prev_shift:
		if next_shift:
			end_date = frappe.db.get_value("Shift Assignment", next_shift, "end_date")
			frappe.db.set_value("Shift Assignment", next_shift, "docstatus", 2)
			frappe.delete_doc("Shift Assignment", next_shift)
		frappe.db.set_value("Shift Assignment", prev_shift, "end_date", end_date or None)

	elif next_shift:
		frappe.db.set_value("Shift Assignment", next_shift, "start_date", start_date)

	else:
		create_shift_assignment(employee, company, shift_type, start_date, end_date, status)


def get_holidays(month_start: str, month_end: str, employee_filters: dict[str, str]) -> dict[str, list[dict]]:
	holidays = {}

	for employee in frappe.get_list("Employee", filters=employee_filters, pluck="name"):
		if holiday_list := get_holiday_list_for_employee(employee, raise_exception=False):
			holidays[employee] = frappe.get_all(
				"Holiday",
				filters={"parent": holiday_list, "holiday_date": ["between", [month_start, month_end]]},
				fields=["name as holiday", "holiday_date", "description", "weekly_off"],
			)

	return holidays


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

	return group_by_employee(query.run(as_dict=True))


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

	return group_by_employee(query.run(as_dict=True))


def group_by_employee(events: list[dict]) -> dict[str, list[dict]]:
	grouped_events = {}
	for event in events:
		grouped_events.setdefault(event["employee"], []).append(
			{k: v for k, v in event.items() if k != "employee"}
		)
	return grouped_events
