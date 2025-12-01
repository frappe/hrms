import frappe
from frappe.query_builder import Case


def execute():
	advance_doctypes = ["Employee Advance", "Leave Encashment", "Gratuity"]

	update_payment_entry(advance_doctypes)
	update_journal_entry(advance_doctypes)


def update_payment_entry(advance_doctypes):
	pe = frappe.qb.DocType("Payment Entry")
	per = frappe.qb.DocType("Payment Entry Reference")
	advance_ledger = frappe.qb.DocType("Advance Payment Ledger Entry")

	(
		frappe.qb.update(pe)
		.inner_join(per)
		.on(per.parent.eq(pe.name))
		.inner_join(advance_ledger)
		.on(
			advance_ledger.voucher_no.eq(pe.name)
			& advance_ledger.voucher_type.eq("Payment Entry")
			& advance_ledger.against_voucher_type.eq(per.reference_doctype)
			& advance_ledger.against_voucher_no.eq(per.reference_name)
		)
		.set(advance_ledger.amount, per.allocated_amount)
		.where(
			per.reference_doctype.isin(advance_doctypes)
			& pe.docstatus.eq(1)
			& pe.payment_type.eq("Pay")
			& (advance_ledger.amount < 0)
		)
	).run()


def update_journal_entry(advance_doctypes):
	je = frappe.qb.DocType("Journal Entry")
	jea = frappe.qb.DocType("Journal Entry Account")
	advance_ledger = frappe.qb.DocType("Advance Payment Ledger Entry")

	(
		frappe.qb.update(jea)
		.inner_join(je)
		.on(je.name == jea.parent)
		.inner_join(advance_ledger)
		.on(
			advance_ledger.voucher_type.eq("Journal Entry")
			& advance_ledger.voucher_no.eq(je.name)
			& advance_ledger.against_voucher_type.eq(jea.reference_type)
			& advance_ledger.against_voucher_no.eq(jea.reference_name)
		)
		.set(
			advance_ledger.amount,
			Case()
			.when(
				(jea.debit_in_account_currency > 0) & (advance_ledger.amount <= 0),
				jea.debit_in_account_currency,
			)
			.when(
				(jea.credit_in_account_currency > 0) & (advance_ledger.amount >= 0),
				jea.credit_in_account_currency * -1,
			)
			.else_(advance_ledger.amount),
		)
		.where(
			jea.reference_type.isin(advance_doctypes)
			& jea.docstatus.eq(1)
			& (
				((jea.debit_in_account_currency > 0) & (advance_ledger.amount <= 0))
				| ((jea.credit_in_account_currency > 0) & (advance_ledger.amount >= 0))
			)
		)
	).run()
