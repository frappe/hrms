# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe

from hrms.tests.utils import HRMSTestSuite


class TestEmployeeTaxExemptionSubCategory(HRMSTestSuite):
	def test_sub_category_limit_under_unlimited_category(self):
		category = frappe.get_doc(
			{
				"doctype": "Employee Tax Exemption Category",
				"name": "_Test Unlimited Category",
				"max_amount": 0,
			}
		).insert()
		sub_category = frappe.get_doc(
			{
				"doctype": "Employee Tax Exemption Sub Category",
				"name": "_Test Capped Sub Category",
				"exemption_category": category.name,
				"max_amount": 50000,
			}
		).insert()
		self.assertEqual(sub_category.max_amount, 50000)

		category.max_amount = 10000
		category.save()
		sub_category.max_amount = 20000
		self.assertRaises(frappe.ValidationError, sub_category.save)
