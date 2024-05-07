import frappe


@frappe.whitelist()
def get_employees(filters: dict | None = None) -> list[dict[str, str]]:
	if not filters:
		filters = {}
	filters["status"] = "Active"
	return frappe.get_list(
		"Employee", filters=filters, fields=["name", "employee_name", "designation", "image"]
	)


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


@frappe.whitelist()
def get_shift_assignment(name: str) -> dict[str, str]:
	return frappe.get_doc("Shift Assignment", name).as_dict()


@frappe.whitelist()
def update_shift_assignment(name: str, values: dict[str, str]) -> None:
	frappe.db.set_value("Shift Assignment", name, values)
