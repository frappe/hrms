# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from frappe.model.document import Document


class ExpenseClaimType(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.expense_claim_account.expense_claim_account import ExpenseClaimAccount

		accounts: DF.Table[ExpenseClaimAccount]
		deferred_expense_account: DF.Check
		description: DF.SmallText | None
		expense_type: DF.Data
	# end: auto-generated types

	def validate(self):
		self.validate_accounts()
		self.validate_repeating_companies()

	def validate_repeating_companies(self):
		"""Error when Same Company is entered multiple times in accounts"""
		accounts_list = []
		for entry in self.accounts:
			accounts_list.append(entry.company)

		if len(accounts_list) != len(set(accounts_list)):
			frappe.throw(_("Same Company is entered more than once"))

	def validate_accounts(self):
		for entry in self.accounts:
			"""Error when Company of Ledger account doesn't match with Company Selected"""
			if frappe.db.get_value("Account", entry.default_account, "company") != entry.company:
				frappe.throw(
					_("Account {0} does not match with Company {1}").format(
						entry.default_account, entry.company
					)
				)
