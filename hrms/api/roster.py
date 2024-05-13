import frappe


@frappe.whitelist()
def get_values(
	doctype: str,
	name: str,
	fields: list,
) -> dict[str, str]:
	return frappe.db.get_value(doctype, name, fields, as_dict=True)


@frappe.whitelist()
def get_events(month_start: str, month_end: str) -> dict[str, list[dict]]:
	shifts = get_shifts(month_start, month_end)
	holidays = get_holidays(month_start, month_end)

	events = shifts.copy()
	for key, value in holidays.items():
		if key in events:
			events[key].extend(value)
		else:
			events[key] = value
	return events


def get_shifts(month_start: str, month_end: str) -> dict[str, list[dict]]:
	ShiftAssignment = frappe.qb.DocType("Shift Assignment")
	ShiftType = frappe.qb.DocType("Shift Type")
	shifts = (
		frappe.qb.select(
			ShiftAssignment.name,
			ShiftAssignment.employee,
			ShiftAssignment.shift_type,
			ShiftAssignment.start_date,
			ShiftAssignment.end_date,
			ShiftAssignment.status,
			ShiftType.start_time,
			ShiftType.end_time,
		)
		.from_(ShiftAssignment)
		.left_join(ShiftType)
		.on(ShiftAssignment.shift_type == ShiftType.name)
		.where(
			(ShiftAssignment.docstatus == 1)
			& (ShiftAssignment.start_date <= month_end)
			& ((ShiftAssignment.end_date >= month_start) | (ShiftAssignment.end_date.isnull()))
		)
	).run(as_dict=True)

	# group shifts under employee by converting list to dict
	grouped_shifts = {}
	for shift in shifts:
		grouped_shifts.setdefault(shift["employee"], []).append(
			{k: v for k, v in shift.items() if k != "employee"}
		)
	return grouped_shifts


def get_holidays(month_start: str, month_end: str) -> dict[str, list[dict]]:
	Employee = frappe.qb.DocType("Employee")
	HolidayList = frappe.qb.DocType("Holiday List")
	Holiday = frappe.qb.DocType("Holiday")
	holidays = (
		frappe.qb.select(
			Employee.employee,
			Holiday.name,
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
	).run(as_dict=True)

	# group holidays under employee by converting list to dict
	grouped_holidays = {}
	for holiday in holidays:
		grouped_holidays.setdefault(holiday["employee"], []).append(
			{k: v for k, v in holiday.items() if k != "employee"}
		)
	return grouped_holidays
