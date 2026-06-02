import frappe

DEMO_COMPANY = "Sparrow Tech Pvt Ltd"
DEMO_COMPANY_ABBR = "ST"
EXPENSE_TYPE_ACCOUNTS = {
	"Travel": f"Travel Expenses - {DEMO_COMPANY_ABBR}",
	"Others": f"Miscellaneous Expenses - {DEMO_COMPANY_ABBR}",
	"Calls": f"Miscellaneous Expenses - {DEMO_COMPANY_ABBR}",
	"Food": f"Miscellaneous Expenses - {DEMO_COMPANY_ABBR}",
	"Medical": f"Miscellaneous Expenses - {DEMO_COMPANY_ABBR}",
}


def setup_expense_claim_type_accounts():
	if not frappe.db.exists("Company", DEMO_COMPANY):
		return

	for exp_type, default_account in EXPENSE_TYPE_ACCOUNTS.items():
		if not frappe.db.exists("Expense Claim Type", exp_type) or not frappe.db.exists(
			"Account", default_account
		):
			continue

		expense_claim_type = frappe.get_doc("Expense Claim Type", exp_type)
		for acc in expense_claim_type.accounts:
			if acc.company == DEMO_COMPANY:
				acc.default_account = default_account
				break
		else:
			expense_claim_type.append(
				"accounts", {"company": DEMO_COMPANY, "default_account": default_account}
			)

		expense_claim_type.save(ignore_permissions=True)
