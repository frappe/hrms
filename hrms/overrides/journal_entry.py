import frappe
from frappe import _
from frappe.utils import flt

from erpnext.accounts.doctype.journal_entry.journal_entry import JournalEntry


class HRMSJournalEntry(JournalEntry):
	def validate_debit_credit_amount(self):
		if not (self.voucher_type == "Exchange Gain Or Loss" and self.multi_currency):
			for d in self.get("accounts"):
				if not flt(d.debit) and not flt(d.credit) and d.reference_type != "Payroll Entry":
					frappe.throw(_("Row {0}: Both Debit and Credit values cannot be zero").format(d.idx))
