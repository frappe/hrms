# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import random_string

from erpnext.accounts.doctype.account.account import get_account_currency


class TestCompany(IntegrationTestCase):
	def test_payroll_account_allows_previous_currency_during_company_currency_change(self):
		company = self.make_company()

		account = company.default_payroll_payable_account
		self.assertEqual(get_account_currency(account), "INR")
		company.default_currency = "USD"
		company.save()

		self.assertEqual(company.default_currency, "USD")
		self.assertEqual(get_account_currency(account), "USD")

	def test_payroll_account_rejects_foreign_currency_without_company_currency_change(self):
		company = self.make_company()
		account = frappe.get_doc("Account", company.default_payroll_payable_account)
		account.account_currency = "USD"
		account.save()

		with self.assertRaisesRegex(frappe.ValidationError, "Default Payroll Payable Account"):
			company.save()

	def make_company(self):
		company = frappe.get_doc(
			{
				"doctype": "Company",
				"company_name": f"HRMS Currency Change {random_string(5)}",
				"abbr": random_string(4),
				"country": "India",
				"default_currency": "INR",
			}
		).insert()
		company.reload()
		self.assertTrue(company.default_payroll_payable_account)
		return company
