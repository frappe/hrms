import frappe


def execute():
	frappe.reload_doc("hr", "doctype", "expense_claim")

	claim = frappe.qb.DocType("Expense Claim")
	(
		frappe.qb.update(claim)
		.set(claim.status, "Partially Paid")
		.where(
			(claim.docstatus == 1)
			& (claim.total_amount_reimbursed > 0)
			& (claim.total_amount_reimbursed < claim.grand_total)
			& (claim.status == "Unpaid")
		)
	).run()
