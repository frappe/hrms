import frappe


@frappe.whitelist()
def get_shifts(month_start: str, month_end: str) -> dict[str, list]:
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
