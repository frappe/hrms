# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, now_datetime, today

from erpnext.setup.doctype.employee.test_employee import make_employee
from erpnext.stock.doctype.purchase_receipt.test_purchase_receipt import make_purchase_receipt

from hrms.tests.utils import HRMSTestSuite


class TestFullandFinalStatement(HRMSTestSuite):
	def setUp(self):
		self.setup_fnf()

	def setup_fnf(self):
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

	def test_employee_advance_settlement(self):
		from hrms.hr.doctype.employee_advance.test_employee_advance import (
			make_employee_advance,
			make_payment_entry,
		)

		advance = make_employee_advance(self.employee)
		make_payment_entry(advance)
		advance.reload()

		self.fnf.receivables = []
		self.fnf.get_outstanding_statements()

		advance_rows = [row for row in self.fnf.receivables if row.component == "Employee Advance"]
		self.assertEqual(len(advance_rows), 1)
		self.assertEqual(advance_rows[0].reference_document, advance.name)
		self.assertEqual(advance_rows[0].account, advance.advance_account)
		self.assertEqual(advance_rows[0].amount, advance.paid_amount)
		self.fnf.save()

		jv = self.fnf.create_journal_entry()
		jv.accounts[-1].account = "_Test Bank - _TC"
		jv.cheque_no = "FNF-ADV-001"
		jv.cheque_date = today()
		jv.insert()
		jv.submit()

		advance.reload()
		self.assertEqual(advance.return_amount, advance.paid_amount)
		self.assertEqual(advance.status, "Returned")

	def test_employee_advance_added_after_bootstrap(self):
		from hrms.hr.doctype.employee_advance.test_employee_advance import (
			make_employee_advance,
			make_payment_entry,
		)

		# placeholder rows already exist from bootstrap
		self.assertTrue(any(row.component == "Employee Advance" for row in self.fnf.receivables))

		advance = make_employee_advance(self.employee)
		make_payment_entry(advance)
		advance.reload()

		self.fnf.get_outstanding_statements()
		advance_rows = [row for row in self.fnf.receivables if row.component == "Employee Advance"]
		self.assertEqual([row.reference_document for row in advance_rows], [advance.name])
		self.assertEqual(advance_rows[0].amount, advance.paid_amount)

		# calling again neither duplicates the advance nor re-adds the placeholder
		self.fnf.get_outstanding_statements()
		advance_rows = [row for row in self.fnf.receivables if row.component == "Employee Advance"]
		self.assertEqual([row.reference_document for row in advance_rows], [advance.name])

	def test_employee_advance_row_refreshed_to_current_balance(self):
		from hrms.hr.doctype.employee_advance.employee_advance import make_return_entry
		from hrms.hr.doctype.employee_advance.test_employee_advance import (
			make_employee_advance,
			make_payment_entry,
		)

		advance = make_employee_advance(self.employee)
		make_payment_entry(advance)
		advance.reload()
		self.fnf.get_outstanding_statements()
		advance_row = next(row for row in self.fnf.receivables if row.reference_document == advance.name)
		self.assertEqual(advance_row.amount, advance.paid_amount)

		# a partial return after the row was created reduces the outstanding balance
		return_entry = frappe.get_doc(
			make_return_entry(
				employee=advance.employee,
				company=advance.company,
				employee_advance_name=advance.name,
				return_amount=300,
				advance_account=advance.advance_account,
				mode_of_payment=advance.mode_of_payment,
				currency=advance.currency,
			)
		)
		return_entry.insert()
		return_entry.submit()
		advance.reload()
		self.assertEqual(advance.return_amount, 300)

		self.fnf.get_outstanding_statements()
		advance_row = next(row for row in self.fnf.receivables if row.reference_document == advance.name)
		self.assertEqual(advance_row.amount, advance.paid_amount - 300)

		# a row with a blank status is refreshed like an unsettled one
		advance_row.status = None
		advance_row.amount = 100
		self.fnf.get_outstanding_statements()
		advance_row = next(row for row in self.fnf.receivables if row.reference_document == advance.name)
		self.assertEqual(advance_row.amount, advance.paid_amount - 300)

		# a row the user has already settled is left as it is
		advance_row.status = "Settled"
		advance_row.amount = 100
		self.fnf.get_outstanding_statements()
		advance_row = next(row for row in self.fnf.receivables if row.reference_document == advance.name)
		self.assertEqual(advance_row.amount, 100)

	def test_employee_advance_rows_follow_employee_change(self):
		from hrms.hr.doctype.employee_advance.test_employee_advance import (
			make_employee_advance,
			make_payment_entry,
		)

		advance = make_employee_advance(self.employee)
		make_payment_entry(advance)
		self.fnf.get_outstanding_statements()
		self.assertIn(advance.name, [row.reference_document for row in self.fnf.receivables])

		other_employee = make_employee(
			"test_fnf_other@example.com", company="_Test Company", relieving_date=add_days(today(), 30)
		)
		self.fnf.employee = other_employee
		self.fnf.relieving_date = add_days(today(), 30)
		self.fnf.get_outstanding_statements()

		advance_rows = [row for row in self.fnf.receivables if row.component == "Employee Advance"]
		self.assertEqual(len(advance_rows), 1)
		self.assertFalse(advance_rows[0].reference_document)

	def test_status_on_discard(self):
		self.fnf.discard()
		self.fnf.reload()
		self.assertEqual(self.fnf.status, "Cancelled")


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
	movement.transaction_date = now_datetime()

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
	asset.save()
	asset.submit()
	return asset_name
