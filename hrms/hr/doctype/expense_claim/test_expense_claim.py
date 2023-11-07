# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt, nowdate, random_string

from erpnext.accounts.doctype.account.test_account import create_account
from erpnext.accounts.doctype.payment_entry.test_payment_entry import get_payment_entry
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.expense_claim.expense_claim import (
	make_bank_entry,
	make_expense_claim_for_delivery_trip,
)

test_dependencies = ["Employee"]
company_name = "_Test Company 3"


class TestExpenseClaim(FrappeTestCase):
	def setUp(self):
		if not frappe.db.get_value("Cost Center", {"company": company_name}):
			cost_center = frappe.new_doc("Cost Center")
			cost_center.update(
				{
					"doctype": "Cost Center",
					"cost_center_name": "_Test Cost Center 3",
					"parent_cost_center": "_Test Company 3 - _TC3",
					"is_group": 0,
					"company": company_name,
				}
			).insert()

			frappe.db.set_value("Company", company_name, "default_cost_center", cost_center)

	def test_total_expense_claim_for_project(self):
		frappe.db.delete("Task")
		frappe.db.delete("Project")
		frappe.db.sql("update `tabExpense Claim` set project = '', task = ''")

		project = create_project("_Test Project 1")

		task = frappe.new_doc("Task")
		task.update(
			dict(doctype="Task", subject="_Test Project Task 1", status="Open", project=project)
		).insert()
		task = task.name

		payable_account = get_payable_account(company_name)

		make_expense_claim(
			payable_account, 300, 200, company_name, "Travel Expenses - _TC3", project, task
		)

		self.assertEqual(frappe.db.get_value("Task", task, "total_expense_claim"), 200)
		self.assertEqual(frappe.db.get_value("Project", project, "total_expense_claim"), 200)

		expense_claim2 = make_expense_claim(
			payable_account, 600, 500, company_name, "Travel Expenses - _TC3", project, task
		)

		self.assertEqual(frappe.db.get_value("Task", task, "total_expense_claim"), 700)
		self.assertEqual(frappe.db.get_value("Project", project, "total_expense_claim"), 700)

		expense_claim2.cancel()

		self.assertEqual(frappe.db.get_value("Task", task, "total_expense_claim"), 200)
		self.assertEqual(frappe.db.get_value("Project", project, "total_expense_claim"), 200)

	def test_expense_claim_status_as_payment_from_journal_entry(self):
		# Via Journal Entry
		payable_account = get_payable_account(company_name)
		expense_claim = make_expense_claim(
			payable_account, 300, 200, company_name, "Travel Expenses - _TC3"
		)

		je = make_journal_entry(expense_claim)

		expense_claim.load_from_db()
		self.assertEqual(expense_claim.status, "Paid")

		je.cancel()
		expense_claim.load_from_db()
		self.assertEqual(expense_claim.status, "Unpaid")

		# expense claim without any sanctioned amount should not have status as Paid
		claim = make_expense_claim(payable_account, 1000, 0, "_Test Company", "Travel Expenses - _TC")
		self.assertEqual(claim.total_sanctioned_amount, 0)
		self.assertEqual(claim.status, "Submitted")

		# no gl entries created
		gl_entry = frappe.get_all(
			"GL Entry", {"voucher_type": "Expense Claim", "voucher_no": claim.name}
		)
		self.assertEqual(len(gl_entry), 0)

	def test_expense_claim_status_as_payment_from_payment_entry(self):
		# Via Payment Entry
		payable_account = get_payable_account(company_name)

		expense_claim = make_expense_claim(
			payable_account, 300, 200, company_name, "Travel Expenses - _TC3"
		)

		pe = make_payment_entry(expense_claim, 200)

		expense_claim.load_from_db()
		self.assertEqual(expense_claim.status, "Paid")

		pe.cancel()
		expense_claim.load_from_db()
		self.assertEqual(expense_claim.status, "Unpaid")

	def test_expense_claim_status_as_payment_allocation_using_pr(self):
		# Allocation via Payment Reconciliation Tool for mutiple employees using journal entry
		payable_account = get_payable_account(company_name)
		# Make employee
		employee = frappe.db.get_value(
			"Employee",
			{"status": "Active", "company": company_name, "first_name": "test_employee1@expenseclaim.com"},
			"name",
		)
		if not employee:
			employee = make_employee("test_employee1@expenseclaim.com", company=company_name)

		expense_claim1 = make_expense_claim(
			payable_account, 300, 200, company_name, "Travel Expenses - _TC3"
		)

		expense_claim2 = make_expense_claim(
			payable_account, 300, 200, company_name, "Travel Expenses - _TC3", employee=employee
		)

		je = make_journal_entry(expense_claim1, do_not_submit=True)
		# Remove expense claim reference from journal entry
		for entry in je.get("accounts"):
			entry.reference_type = ""
			entry.reference_name = ""

			cost_center = entry.cost_center
			if entry.party:
				employee1 = entry.party

			if not entry.party_type:
				entry.credit += 200
				entry.credit_in_account_currency += 200

		je.append(
			"accounts",
			{
				"account": payable_account,
				"debit_in_account_currency": 200,
				"reference_type": "Expense Claim",
				"party_type": "Employee",
				"party": employee,
				"cost_center": cost_center,
			},
		)

		je.save()
		je.submit()

		allocate_using_payment_reconciliation(expense_claim1, employee1, je, payable_account)
		expense_claim1.load_from_db()
		self.assertEqual(expense_claim1.status, "Paid")

		allocate_using_payment_reconciliation(expense_claim2, employee, je, payable_account)
		expense_claim2.load_from_db()
		self.assertEqual(expense_claim2.status, "Paid")

	def test_expense_claim_against_fully_paid_advances(self):
		from hrms.hr.doctype.employee_advance.test_employee_advance import (
			get_advances_for_claim,
			make_employee_advance,
			make_journal_entry_for_advance,
		)

		frappe.db.delete("Employee Advance")

		payable_account = get_payable_account("_Test Company")
		claim = make_expense_claim(
			payable_account, 1000, 1000, "_Test Company", "Travel Expenses - _TC", do_not_submit=True
		)

		advance = make_employee_advance(claim.employee)
		pe = make_journal_entry_for_advance(advance)
		pe.submit()

		# claim for already paid out advances
		claim = get_advances_for_claim(claim, advance.name)
		claim.save()
		claim.submit()

		self.assertEqual(claim.grand_total, 0)
		self.assertEqual(claim.status, "Paid")

	def test_advance_amount_allocation_against_claim_with_taxes(self):
		from hrms.hr.doctype.employee_advance.test_employee_advance import (
			get_advances_for_claim,
			make_employee_advance,
			make_journal_entry_for_advance,
		)

		frappe.db.delete("Employee Advance")

		payable_account = get_payable_account("_Test Company")
		taxes = generate_taxes("_Test Company")
		claim = make_expense_claim(
			payable_account,
			700,
			700,
			"_Test Company",
			"Travel Expenses - _TC",
			do_not_submit=True,
			taxes=taxes,
		)
		claim.save()

		advance = make_employee_advance(claim.employee)
		pe = make_journal_entry_for_advance(advance)
		pe.submit()

		# claim for already paid out advances
		claim = get_advances_for_claim(claim, advance.name, 763)
		claim.save()
		claim.submit()

		self.assertEqual(claim.grand_total, 0)
		self.assertEqual(claim.status, "Paid")

	def test_expense_claim_partially_paid_via_advance(self):
		from hrms.hr.doctype.employee_advance.test_employee_advance import (
			get_advances_for_claim,
			make_employee_advance,
			make_journal_entry_for_advance,
		)

		frappe.db.delete("Employee Advance")

		payable_account = get_payable_account("_Test Company")
		claim = make_expense_claim(
			payable_account, 1000, 1000, "_Test Company", "Travel Expenses - _TC", do_not_submit=True
		)

		# link advance for partial amount
		advance = make_employee_advance(claim.employee, {"advance_amount": 500})
		pe = make_journal_entry_for_advance(advance)
		pe.submit()

		claim = get_advances_for_claim(claim, advance.name)
		claim.save()
		claim.submit()

		self.assertEqual(claim.grand_total, 500)
		self.assertEqual(claim.status, "Unpaid")

		# reimburse remaning amount
		make_payment_entry(claim, 500)
		claim.reload()

		self.assertEqual(claim.total_amount_reimbursed, 500)
		self.assertEqual(claim.status, "Paid")

	def test_expense_claim_gl_entry(self):
		payable_account = get_payable_account(company_name)
		taxes = generate_taxes()
		expense_claim = make_expense_claim(
			payable_account,
			300,
			200,
			company_name,
			"Travel Expenses - _TC3",
			do_not_submit=True,
			taxes=taxes,
		)
		expense_claim.submit()

		gl_entries = frappe.db.sql(
			"""select account, debit, credit
			from `tabGL Entry` where voucher_type='Expense Claim' and voucher_no=%s
			order by account asc""",
			expense_claim.name,
			as_dict=1,
		)

		self.assertTrue(gl_entries)

		expected_values = dict(
			(d[0], d)
			for d in [
				["Output Tax CGST - _TC3", 18.0, 0.0],
				[payable_account, 0.0, 218.0],
				["Travel Expenses - _TC3", 200.0, 0.0],
			]
		)

		for gle in gl_entries:
			self.assertEqual(expected_values[gle.account][0], gle.account)
			self.assertEqual(expected_values[gle.account][1], gle.debit)
			self.assertEqual(expected_values[gle.account][2], gle.credit)

	def test_invalid_gain_loss_for_expense_claim(self):
		payable_account = get_payable_account(company_name)
		taxes = generate_taxes()
		expense_claim = make_expense_claim(
			payable_account,
			300,
			200,
			company_name,
			"Travel Expenses - _TC3",
			do_not_submit=True,
			taxes=taxes,
		)
		expense_claim.submit()

		from hrms.overrides.employee_payment_entry import get_payment_entry_for_employee

		pe = get_payment_entry_for_employee(expense_claim.doctype, expense_claim.name)
		pe.save()
		pe.submit()
		self.assertEqual(len(pe.references), 1)
		self.assertEqual(pe.references[0].exchange_gain_loss, 0.0)
		self.assertEqual(pe.references[0].exchange_rate, 1.0)
		# Invalid gain/loss JE shouldn't be created for base currency Expense Claims
		self.assertEqual(
			frappe.db.get_all(
				"Journal Entry Account",
				filters={
					"reference_type": expense_claim.doctype,
					"reference_name": expense_claim.name,
					"docstatus": 1,
				},
			),
			[],
		)

	def test_rejected_expense_claim(self):
		payable_account = get_payable_account(company_name)
		expense_claim = frappe.get_doc(
			{
				"doctype": "Expense Claim",
				"employee": "_T-Employee-00001",
				"payable_account": payable_account,
				"approval_status": "Rejected",
				"expenses": [
					{
						"expense_type": "Travel",
						"default_account": "Travel Expenses - _TC3",
						"amount": 300,
						"sanctioned_amount": 200,
					}
				],
			}
		)
		expense_claim.submit()

		self.assertEqual(expense_claim.status, "Rejected")
		self.assertEqual(expense_claim.total_sanctioned_amount, 0.0)

		gl_entry = frappe.get_all(
			"GL Entry", {"voucher_type": "Expense Claim", "voucher_no": expense_claim.name}
		)
		self.assertEqual(len(gl_entry), 0)

	def test_expense_approver_perms(self):
		user = "test_approver_perm_emp@example.com"
		make_employee(user, "_Test Company")

		# check doc shared
		payable_account = get_payable_account("_Test Company")
		expense_claim = make_expense_claim(
			payable_account, 300, 200, "_Test Company", "Travel Expenses - _TC", do_not_submit=True
		)
		expense_claim.expense_approver = user
		expense_claim.save()
		self.assertTrue(expense_claim.name in frappe.share.get_shared("Expense Claim", user))

		# check shared doc revoked
		expense_claim.reload()
		expense_claim.expense_approver = "test@example.com"
		expense_claim.save()
		self.assertTrue(expense_claim.name not in frappe.share.get_shared("Expense Claim", user))

		expense_claim.reload()
		expense_claim.expense_approver = user
		expense_claim.save()

		frappe.set_user(user)
		expense_claim.reload()
		expense_claim.status = "Approved"
		expense_claim.submit()
		frappe.set_user("Administrator")

	def test_multiple_payment_entries_against_expense(self):
		# Creating expense claim
		payable_account = get_payable_account("_Test Company")
		expense_claim = make_expense_claim(
			payable_account, 5500, 5500, "_Test Company", "Travel Expenses - _TC"
		)
		expense_claim.save()
		expense_claim.submit()

		# Payment entry 1: paying 500
		make_payment_entry(expense_claim, 500)
		outstanding_amount, total_amount_reimbursed = get_outstanding_and_total_reimbursed_amounts(
			expense_claim
		)
		self.assertEqual(outstanding_amount, 5000)
		self.assertEqual(total_amount_reimbursed, 500)

		# Payment entry 1: paying 2000
		make_payment_entry(expense_claim, 2000)
		outstanding_amount, total_amount_reimbursed = get_outstanding_and_total_reimbursed_amounts(
			expense_claim
		)
		self.assertEqual(outstanding_amount, 3000)
		self.assertEqual(total_amount_reimbursed, 2500)

		# Payment entry 1: paying 3000
		make_payment_entry(expense_claim, 3000)
		outstanding_amount, total_amount_reimbursed = get_outstanding_and_total_reimbursed_amounts(
			expense_claim
		)
		self.assertEqual(outstanding_amount, 0)
		self.assertEqual(total_amount_reimbursed, 5500)

	def test_expense_claim_against_delivery_trip(self):
		from erpnext.stock.doctype.delivery_trip.test_delivery_trip import (
			create_address,
			create_delivery_trip,
			create_driver,
			create_vehicle,
		)
		from erpnext.tests.utils import create_test_contact_and_address

		driver = create_driver()
		create_vehicle()
		create_test_contact_and_address()
		address = create_address(driver)

		delivery_trip = create_delivery_trip(driver, address)
		expense_claim = make_expense_claim_for_delivery_trip(delivery_trip.name)
		self.assertEqual(delivery_trip.name, expense_claim.delivery_trip)

	def test_journal_entry_against_expense_claim(self):
		payable_account = get_payable_account(company_name)
		taxes = generate_taxes()
		expense_claim = make_expense_claim(
			payable_account,
			300,
			200,
			company_name,
			"Travel Expenses - _TC3",
			do_not_submit=True,
			taxes=taxes,
		)
		expense_claim.submit()

		je = make_journal_entry(expense_claim)

		self.assertEqual(je.accounts[0].debit_in_account_currency, expense_claim.grand_total)

	def test_accounting_dimension_mapping(self):
		project = create_project("_Test Expense Project")
		payable_account = get_payable_account(company_name)

		expense_claim = make_expense_claim(
			payable_account,
			300,
			200,
			company_name,
			"Travel Expenses - _TC3",
			do_not_submit=True,
		)

		expense_claim.expenses[0].project = project
		expense_claim.submit()

		dimensions = frappe.db.get_value(
			"GL Entry",
			{
				"voucher_type": "Expense Claim",
				"voucher_no": expense_claim.name,
				"account": "Travel Expenses - _TC3",
			},
			["cost_center", "project"],
			as_dict=1,
		)

		self.assertEqual(dimensions.project, project)
		self.assertEqual(dimensions.cost_center, expense_claim.cost_center)

	def test_rounding(self):
		payable_account = get_payable_account(company_name)
		taxes = generate_taxes(rate=7)
		expense_claim = make_expense_claim(
			payable_account,
			130.84,
			130.84,
			company_name,
			"Travel Expenses - _TC3",
			taxes=taxes,
		)

		self.assertEqual(expense_claim.total_sanctioned_amount, 130.84)
		self.assertEqual(expense_claim.total_taxes_and_charges, 9.16)
		self.assertEqual(expense_claim.grand_total, 140)

		pe = make_payment_entry(expense_claim, 140)

		expense_claim.reload()
		self.assertEqual(expense_claim.status, "Paid")

		pe.cancel()
		expense_claim.reload()
		self.assertEqual(expense_claim.status, "Unpaid")

	def test_repost(self):
		# Update repost settings
		allowed_types = ["Expense Claim"]
		repost_settings = frappe.get_doc("Repost Accounting Ledger Settings")
		for x in allowed_types:
			repost_settings.append("allowed_types", {"document_type": x, "allowed": True})
		repost_settings.save()

		payable_account = get_payable_account(company_name)
		taxes = generate_taxes(rate=10)
		expense_claim = make_expense_claim(
			payable_account,
			100,
			100,
			company_name,
			"Travel Expenses - _TC3",
			taxes=taxes,
		)
		expected_data = [{"total_debit": 110.0, "total_credit": 110.0}]

		# assert ledger entries
		ledger_balance = frappe.db.get_all(
			"GL Entry",
			filters={"voucher_no": expense_claim.name, "is_cancelled": 0},
			fields=["sum(debit) as total_debit", "sum(credit) as total_credit"],
		)
		self.assertEqual(ledger_balance, expected_data)

		gl_entries = frappe.db.get_all(
			"GL Entry", filters={"account": expense_claim.payable_account, "voucher_no": expense_claim.name}
		)
		self.assertEqual(len(gl_entries), 1)
		frappe.db.set_value("GL Entry", gl_entries[0].name, "credit", 0)

		ledger_balance = frappe.db.get_all(
			"GL Entry",
			filters={"voucher_no": expense_claim.name, "is_cancelled": 0},
			fields=["sum(debit) as total_debit", "sum(credit) as total_credit"],
		)
		self.assertNotEqual(ledger_balance, expected_data)

		# Do a repost
		repost_doc = frappe.new_doc("Repost Accounting Ledger")
		repost_doc.company = expense_claim.company
		repost_doc.append(
			"vouchers", {"voucher_type": expense_claim.doctype, "voucher_no": expense_claim.name}
		)
		repost_doc.save().submit()
		ledger_balance = frappe.db.get_all(
			"GL Entry",
			filters={"voucher_no": expense_claim.name, "is_cancelled": 0},
			fields=["sum(debit) as total_debit", "sum(credit) as total_credit"],
		)
		self.assertEqual(ledger_balance, expected_data)


def get_payable_account(company):
	return frappe.get_cached_value("Company", company, "default_payable_account")


def generate_taxes(company=None, rate=None) -> dict:
	company = company or company_name
	parent_account = frappe.db.get_value(
		"Account", filters={"account_name": "Duties and Taxes", "company": company}
	)
	account = create_account(
		company=company,
		account_name="Output Tax CGST",
		account_type="Tax",
		parent_account=parent_account,
	)

	cost_center = frappe.db.get_value("Company", company, "cost_center")

	return {
		"taxes": [
			{
				"account_head": account,
				"cost_center": cost_center,
				"rate": rate or 9,
				"description": "CGST",
			}
		]
	}


def make_expense_claim(
	payable_account,
	amount,
	sanctioned_amount,
	company,
	account,
	project=None,
	task_name=None,
	do_not_submit=False,
	taxes=None,
	employee=None,
):

	if not employee:
		employee = frappe.db.get_value("Employee", {"status": "Active", "company": company})
		if not employee:
			employee = make_employee("test_employee@expenseclaim.com", company=company)

	currency, cost_center = frappe.db.get_value(
		"Company", company, ["default_currency", "cost_center"]
	)
	expense_claim = {
		"doctype": "Expense Claim",
		"employee": employee,
		"payable_account": payable_account,
		"approval_status": "Approved",
		"company": company,
		"currency": currency,
		"expenses": [
			{
				"expense_type": "Travel",
				"default_account": account,
				"currency": currency,
				"amount": amount,
				"sanctioned_amount": sanctioned_amount,
				"cost_center": cost_center,
			}
		],
	}
	if taxes:
		expense_claim.update(taxes)

	expense_claim = frappe.get_doc(expense_claim)

	if project:
		expense_claim.project = project
	if task_name:
		expense_claim.task = task_name

	if do_not_submit:
		return expense_claim
	expense_claim.submit()
	return expense_claim


def get_outstanding_and_total_reimbursed_amounts(expense_claim):
	outstanding_amount = flt(
		frappe.db.get_value("Expense Claim", expense_claim.name, "total_sanctioned_amount")
	) - flt(frappe.db.get_value("Expense Claim", expense_claim.name, "total_amount_reimbursed"))
	total_amount_reimbursed = flt(
		frappe.db.get_value("Expense Claim", expense_claim.name, "total_amount_reimbursed")
	)

	return outstanding_amount, total_amount_reimbursed


def make_payment_entry(expense_claim, amount):
	from hrms.overrides.employee_payment_entry import get_payment_entry_for_employee

	pe = get_payment_entry_for_employee("Expense Claim", expense_claim.name)
	pe.reference_no = "1"
	pe.reference_date = nowdate()
	pe.source_exchange_rate = 1
	pe.references[0].allocated_amount = amount
	pe.insert()
	pe.submit()

	return pe


def make_journal_entry(expense_claim, do_not_submit=False):
	je_dict = make_bank_entry("Expense Claim", expense_claim.name)
	je = frappe.get_doc(je_dict)
	je.posting_date = nowdate()
	je.cheque_no = random_string(5)
	je.cheque_date = nowdate()

	if not do_not_submit:
		je.submit()

	return je


def create_payment_reconciliation(company, employee, payable_account):
	pr = frappe.new_doc("Payment Reconciliation")
	pr.company = company
	pr.party_type = "Employee"
	pr.party = employee
	pr.receivable_payable_account = payable_account
	pr.from_invoice_date = pr.to_invoice_date = pr.from_payment_date = pr.to_payment_date = nowdate()
	return pr


def allocate_using_payment_reconciliation(expense_claim, employee, journal_entry, payable_account):
	pr = create_payment_reconciliation(company_name, employee, payable_account)
	pr.get_unreconciled_entries()
	invoices = [x.as_dict() for x in pr.get("invoices") if x.invoice_number == expense_claim.name]
	payments = [x.as_dict() for x in pr.get("payments") if x.reference_name == journal_entry.name]

	pr.allocate_entries(frappe._dict({"invoices": invoices, "payments": payments}))
	pr.reconcile()


def create_project(project_name):
	project = frappe.db.exists("Project", {"project_name": project_name})
	if project:
		return project

	doc = frappe.new_doc("Project")
	doc.project_name = project_name
	doc.insert()
	return doc.name
