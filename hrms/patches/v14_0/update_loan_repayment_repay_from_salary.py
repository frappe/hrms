import frappe


def execute():
	if frappe.db.exists("Custom Field", "Loan Repayment-repay_from_salary"):
		frappe.db.set_value(
			"Custom Field",
			"Loan Repayment-repay_from_salary",
			{"fetch_from": None, "fetch_if_empty": 0},
		)
