# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from erpnext.assets.doctype.asset.test_asset import create_asset_data
from erpnext.setup.doctype.employee.test_employee import make_employee
from erpnext.stock.doctype.purchase_receipt.test_purchase_receipt import make_purchase_receipt


class TestFullandFinalStatement(IntegrationTestCase):
	def setUp(self):
		for dt in ["Full and Final Statement", "Asset", "Asset Movement", "Asset Movement Item"]:
			frappe.db.delete(dt)

		self.setup_fnf()

	def setup_fnf(self):
		create_asset_data()

		self.employee = make_employee(
			"test_fnf@example.com", company="_Test Company", relieving_date=add_days(today(), 30)
		)
		self.movement = create_asset_movement(self.employee)
		self.fnf = create_full_and_final_statement(self.employee)

	def test_check_bootstraped_data_asset_movement_and_jv_creation(self):
		payables_bootstraped_component = [
			"Gratuity",
			"Expense Claim",
			"Bonus",
			"Leave Encashment",
		]

		receivable_bootstraped_component = self.fnf.get_receivable_component()

		# checking payables and receivables bootstraped value
		self.assertEqual([payable.component for payable in self.fnf.payables], payables_bootstraped_component)
		self.assertEqual(
			[receivable.component for receivable in self.fnf.receivables], receivable_bootstraped_component
		)

		# checking allocated asset
		self.assertIn(self.movement, [asset.reference for asset in self.fnf.assets_allocated])

	def test_asset_cost(self):
		self.fnf.receivables[0].amount = 50000

		self.fnf.assets_allocated[0].action = "Recover Cost"
		self.fnf.save()

		self.assertEqual(self.fnf.assets_allocated[0].actual_cost, 100000.0)
		self.assertEqual(self.fnf.assets_allocated[0].cost, 100000.0)
		self.assertEqual(self.fnf.total_asset_recovery_cost, 100000.0)
		self.assertEqual(self.fnf.total_receivable_amount, 150000.0)

	def test_journal_entry(self):
		self.fnf.receivables[0].amount = 50000
		self.fnf.assets_allocated[0].action = "Recover Cost"
		self.fnf.save()

		jv = self.fnf.create_journal_entry()

		self.assertEqual(jv.accounts[0].credit_in_account_currency, 50000.0)
		self.assertEqual(jv.accounts[1].credit_in_account_currency, 100000.0)

		debit_entry = jv.accounts[-1]
		self.assertEqual(debit_entry.debit_in_account_currency, 150000.0)
		self.assertEqual(debit_entry.reference_type, "Full and Final Statement")
		self.assertEqual(debit_entry.reference_name, self.fnf.name)


def create_full_and_final_statement(employee):
	fnf = frappe.new_doc("Full and Final Statement")
	fnf.employee = employee
	fnf.transaction_date = today()
	fnf.save()
	return fnf


def create_asset_movement(employee):
	asset_name = create_asset()
	movement = frappe.new_doc("Asset Movement")
	movement.company = "_Test Company"
	movement.purpose = "Issue"
	movement.transaction_date = today()

	movement.append("assets", {"asset": asset_name, "to_employee": employee})

	movement.save()
	movement.submit()
	return movement.name


def create_asset():
	pr = make_purchase_receipt(item_code="Macbook Pro", qty=1, rate=100000.0, location="Test Location")

	asset_name = frappe.db.get_value("Asset", {"purchase_receipt": pr.name}, "name")
	asset = frappe.get_doc("Asset", asset_name)
	asset.calculate_depreciation = 0
	asset.available_for_use_date = today()
	asset.submit()
	return asset_name
