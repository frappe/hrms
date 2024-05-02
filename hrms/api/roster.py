import frappe


@frappe.whitelist()
def get_employees(filters: dict | None = None) -> list[dict]:
	if not filters:
		filters = {}
	filters["status"] = "Active"
	return frappe.get_list("Employee", filters=filters, fields=["name", "employee_name"])


@frappe.whitelist()
def get_shifts(filters: dict | None = None, or_filters: dict | None = None) -> list[dict]:
	return frappe.get_list(
		"Shift Assignment",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "employee", "shift_type", "start_date", "end_date"],
	)
