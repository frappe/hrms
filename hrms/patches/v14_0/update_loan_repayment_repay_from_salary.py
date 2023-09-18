import frappe


def execute():
	if frappe.db.exists("Custom Field", {"name": "Loan Repayment-repay_from_salary"}):
		frappe.db.set_value(
			"Custom Field", {"name": "Loan Repayment-repay_from_salary"}, { "fetch_from": None, "fetch_if_empty": 0 }
		)
