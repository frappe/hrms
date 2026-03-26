import frappe
from frappe.query_builder import DocType


def execute():
	"""
	Description:
	Call set_total_advance_paid for advance ledger entries
	"""
	advance_doctpyes = ["Employee Advance", "Leave Encashment", "Gratuity"]

	for doctype in advance_doctpyes:
		if frappe.db.has_table(doctype):
			call_set_total_advance_paid(doctype)


def call_set_total_advance_paid(doctype) -> list:
	aple = DocType("Advance Payment Ledger Entry")
	advance_doctype = DocType(doctype)

	date = frappe.utils.getdate("31-07-2025")

	entries = (
		frappe.qb.from_(aple)
		.left_join(advance_doctype)
		.on(aple.against_voucher_no == advance_doctype.name)
		.select(aple.against_voucher_no, aple.against_voucher_type)
		.where((aple.delinked == 0) & (advance_doctype.creation >= date))
	).run(as_dict=True)

	for entry in entries:
		try:
			advance_payment_ledger = frappe.get_doc(entry.against_voucher_type, entry.against_voucher_no)
			advance_payment_ledger.set_total_advance_paid()
		except Exception as e:
			frappe.log_error(e)
			continue
