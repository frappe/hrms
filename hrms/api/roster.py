import frappe


@frappe.whitelist()
def get_all_employees(filters) -> list:
	return frappe.get_list("Employee", filters=filters, fields="employee_name")
