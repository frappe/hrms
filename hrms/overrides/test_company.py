# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import random_string

from erpnext.setup.doctype.company.company import Company


class TestCompany(IntegrationTestCase):
	def test_payroll_account_allows_previous_currency_during_company_currency_change(self):
		company = self.make_company()

		original_validate_currency = Company.validate_currency

		def validate_currency_with_change_signal(doc):
			original_validate_currency(doc)
			doc.currency_changed = True

		with patch.object(Company, "validate_currency", validate_currency_with_change_signal):
			company.default_currency = "USD"
			company.save()

		self.assertEqual(company.default_currency, "USD")

	def test_payroll_account_rejects_previous_currency_without_company_currency_change(self):
		company = self.make_company()
		company.default_currency = "USD"

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
