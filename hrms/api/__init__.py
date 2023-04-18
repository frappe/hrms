import frappe


@frappe.whitelist()
def get_current_user_info() -> dict:
	current_user = frappe.session.user
	return frappe.db.get_value("User", current_user, ["first_name", "full_name"], as_dict=True)
