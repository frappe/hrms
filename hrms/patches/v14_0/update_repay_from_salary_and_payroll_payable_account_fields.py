import frappe


def execute():
	if frappe.db.exists("Custom Field", {"name": "Loan Repayment-repay_from_salary"}):
		frappe.db.set_value(
			"Custom Field", {"name": "Loan Repayment-repay_from_salary"}, "fetch_if_empty", 1
		)

	if frappe.db.exists("Custom Field", {"name": "Loan Repayment-payroll_payable_account"}):
		frappe.db.set_value(
			"Custom Field",
			{"name": "Loan Repayment-payroll_payable_account"},
			"insert_after",
			"payment_account",
		)
