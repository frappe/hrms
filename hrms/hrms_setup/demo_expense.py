import frappe


def get_expense_type_accounts(company_abbr):
	return {
		"Travel": f"Travel Expenses - {company_abbr}",
		"Others": f"Miscellaneous Expenses - {company_abbr}",
		"Calls": f"Miscellaneous Expenses - {company_abbr}",
		"Food": f"Miscellaneous Expenses - {company_abbr}",
		"Medical": f"Miscellaneous Expenses - {company_abbr}",
	}


def setup_expense_claim_type_accounts():
	from hrms.hrms_setup.demo import get_demo_company_context

	context = get_demo_company_context()
	if not frappe.db.exists("Company", context.demo_company):
		return

	for exp_type, default_account in get_expense_type_accounts(context.demo_company_abbr).items():
		if not frappe.db.exists("Expense Claim Type", exp_type) or not frappe.db.exists(
			"Account", default_account
		):
			continue

		expense_claim_type = frappe.get_doc("Expense Claim Type", exp_type)
		for acc in expense_claim_type.accounts:
			if acc.company == context.demo_company:
				acc.default_account = default_account
				break
		else:
			expense_claim_type.append(
				"accounts", {"company": context.demo_company, "default_account": default_account}
			)

		expense_claim_type.save(ignore_permissions=True)
