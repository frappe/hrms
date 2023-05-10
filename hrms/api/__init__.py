import frappe


@frappe.whitelist()
def get_current_user_info() -> dict:
	current_user = frappe.session.user
	return frappe.db.get_value("User", current_user, ["first_name", "full_name", "user_image"], as_dict=True)


@frappe.whitelist()
def get_employee_info() -> dict:
	current_user = frappe.session.user
	employee = frappe.db.get_value(
		"Employee",
		{"user_id": current_user},
		["name", "employee_name", "designation", "department", "company", "reports_to"],
		as_dict=True
	)
	return employee
