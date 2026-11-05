# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt

import frappe
from frappe.utils import random_string

from hrms.tests.utils import HRMSTestSuite

# test_records = frappe.get_test_records('Expense Claim Type')


class TestExpenseClaimType(HRMSTestSuite):
	def test_default_account_must_be_expense_ledger(self):
		def make_claim_type(account):
			return frappe.get_doc(
				{
					"doctype": "Expense Claim Type",
					"expense_type": f"_Test Claim Type {random_string(5)}",
					"accounts": [{"company": "_Test Company", "default_account": account}],
				}
			)

		self.assertRaises(frappe.ValidationError, make_claim_type("_Test Bank - _TC").insert)
		self.assertRaises(frappe.ValidationError, make_claim_type("Indirect Expenses - _TC").insert)
		self.assertTrue(make_claim_type("Travel Expenses - _TC").insert().name)
