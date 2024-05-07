import frappe


def execute():
	frappe.reload_doc("setup", "doctype", "company")

	companies = frappe.get_all("Company", fields=["name", "default_payable_account"])

	for company in companies:
		if not company.default_expense_claim_payable_account and company.default_payable_account:
			frappe.db.set_value(
				"Company",
				company.name,
				"default_expense_claim_payable_account",
				company.default_payable_account,
			)
