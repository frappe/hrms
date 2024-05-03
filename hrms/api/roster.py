import frappe


@frappe.whitelist()
def get_employees(filters: dict | None = None) -> list[dict[str, str]]:
	if not filters:
		filters = {}
	filters["status"] = "Active"
	return frappe.get_list("Employee", filters=filters, fields=["name", "employee_name"])


@frappe.whitelist()
def get_shifts(filters: dict | None = None, or_filters: list | dict | None = None) -> dict[str, list]:
	if not filters:
		filters = {}
	filters["docstatus"] = 1

	shifts = frappe.get_list(
		"Shift Assignment",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "employee", "shift_type", "start_date", "end_date", "status"],
	)

	grouped_shifts = {}
	for shift in shifts:
		grouped_shifts.setdefault(shift["employee"], []).append(
			{k: v for k, v in shift.items() if k != "employee"}
		)
	return grouped_shifts
