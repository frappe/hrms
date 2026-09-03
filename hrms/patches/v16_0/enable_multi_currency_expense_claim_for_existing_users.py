import frappe


def execute():
	if has_multi_currency_documents("Expense Claim") or has_multi_currency_documents("Employee Advance"):
		frappe.db.set_single_value("HR Settings", "enable_multi_currency_expense_claim", 1)


def has_multi_currency_documents(doctype: str) -> bool:
	Doc = frappe.qb.DocType(doctype)
	Company = frappe.qb.DocType("Company")

	return bool(
		(
			frappe.qb.from_(Doc)
			.join(Company)
			.on(Doc.company == Company.name)
			.select(Doc.name)
			.where(Doc.currency != Company.default_currency)
			.limit(1)
		).run()
	)
