import frappe

DEMO_COMPANY = "Sparrow Tech Pvt Ltd"
EXPENSE_TYPE_ACCOUNTS = {
	"Travel": "Travel Expenses",
	"Others": "Miscellaneous Expenses",
	"Calls": "Miscellaneous Expenses",
	"Food": "Miscellaneous Expenses",
	"Medical": "Miscellaneous Expenses",
}


def setup_expense_claim_type_accounts():
	company = get_demo_company()
	if not company:
		return

	for exp_type, account_name in EXPENSE_TYPE_ACCOUNTS.items():
		if not frappe.db.exists("Expense Claim Type", exp_type):
			continue

		default_account = get_expense_account(company, account_name)
		if not default_account:
			continue

		expense_claim_type = frappe.get_doc("Expense Claim Type", exp_type)
		for acc in expense_claim_type.accounts:
			if acc.company == company:
				acc.default_account = default_account
				break
		else:
			expense_claim_type.append("accounts", {"company": company, "default_account": default_account})

		expense_claim_type.save(ignore_permissions=True)


def get_demo_company():
	return frappe.db.exists("Company", DEMO_COMPANY) or frappe.db.get_value("Company", {}, "name")


def get_expense_account(company, account_name):
	account = frappe.db.get_value(
		"Account",
		{
			"company": company,
			"account_name": account_name,
			"is_group": 0,
			"root_type": "Expense",
		},
		"name",
	)
	return account or frappe.db.get_value(
		"Account",
		{"company": company, "is_group": 0, "root_type": "Expense"},
		"name",
	)
