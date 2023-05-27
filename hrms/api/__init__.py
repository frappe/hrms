import frappe


@frappe.whitelist()
def get_current_user_info() -> dict:
	current_user = frappe.session.user
	return frappe.db.get_value(
		"User", current_user, ["first_name", "full_name", "user_image"], as_dict=True
	)


@frappe.whitelist()
def get_current_employee_info() -> dict:
	current_user = frappe.session.user
	employee = frappe.db.get_value(
		"Employee",
		{"user_id": current_user},
		["name", "employee_name", "designation", "department", "company", "reports_to", "user_id"],
		as_dict=True,
	)
	return employee


@frappe.whitelist()
def get_employees(employee: str = None) -> list[dict]:
	filters = []
	if employee:
		filters["name"] = employee

	return frappe.db.get_all(
		"Employee",
		filters=filters,
		fields=[
			"name",
			"employee_name",
			"designation",
			"department",
			"company",
			"reports_to",
			"user_id",
			"image",
			"status",
		],
	)


@frappe.whitelist()
def get_leave_applications(filters: dict = {}) -> list[dict]:
	doctype = "Leave Application"
	leave_applications = frappe.get_list(
		"Leave Application",
		fields=["name", "employee", "employee_name", "leave_type", "status", "from_date", "to_date", "half_day", "half_day_date", "description", "total_leave_days", "leave_balance", "leave_approver", "posting_date"],
		filters=filters,
		order_by="from_date desc",
	)

	for leave in leave_applications:
		leave.can_cancel = frappe.has_permission(doctype, "cancel", user=frappe.session.user)
		leave.can_delete = frappe.has_permission(doctype, "delete", user=frappe.session.user)

	return leave_applications


@frappe.whitelist()
def get_employee_leave_applications(employee: str) -> list[dict]:
	filters = {
		"employee": employee,
		"status": ["!=", "Cancelled"]
	}

	return get_leave_applications(filters)


@frappe.whitelist()
def get_team_leave_applications(employee: str, user_id: str) -> list[dict]:
	filters = {
		"employee": ["!=", employee],
		"leave_approver": user_id,
		"status": ["!=", "Cancelled"],
	}

	return get_leave_applications(filters)