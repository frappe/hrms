import frappe
from frappe.query_builder.functions import IfNull


def execute():
	ExpenseClaimAdvance = frappe.qb.DocType("Expense Claim Advance")

	(
		frappe.qb.update(ExpenseClaimAdvance)
		.set(ExpenseClaimAdvance.reference_name, ExpenseClaimAdvance.payment_entry)
		.set(ExpenseClaimAdvance.reference_type, "Payment Entry")
		.where(
			(IfNull(ExpenseClaimAdvance.payment_entry, "") != "")
			& (IfNull(ExpenseClaimAdvance.reference_name, "") == "")
		)
	).run()
