# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt

import frappe
from frappe.utils import flt, nowdate, random_string, today

from erpnext import get_company_currency
from erpnext.accounts.doctype.account.test_account import create_account
from erpnext.accounts.doctype.payment_entry.test_payment_entry import get_payment_entry
from erpnext.setup.doctype.employee.test_employee import make_employee
from erpnext.setup.utils import get_exchange_rate

from hrms.hr.doctype.expense_claim.expense_claim import (
	MismatchError,
	get_outstanding_amount_for_claim,
	make_bank_entry,
	make_expense_claim_for_delivery_trip,
)
from hrms.tests.utils import HRMSTestSuite

company_name = "_Test Company 3"


class TestExpenseClaim(HRMSTestSuite):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.make_employees()

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
		frappe.db.set_value("Account", "Employee Advances - _TC", "account_type", "Receivable")

	def tearDown(self):
		frappe.set_user("Administrator")

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
			payable_account, 300, 200, company_name, "Travel Expenses - _TC3", project=project, task_name=task
		)

		self.assertEqual(frappe.db.get_value("Task", task, "total_expense_claim"), 200)
		self.assertEqual(frappe.db.get_value("Project", project, "total_expense_claim"), 200)

		expense_claim2 = make_expense_claim(
			payable_account, 600, 500, company_name, "Travel Expenses - _TC3", project=project, task_name=task
		)

		self.assertEqual(frappe.db.get_value("Task", task, "total_expense_claim"), 700)
		self.assertEqual(frappe.db.get_value("Project", project, "total_expense_claim"), 700)

		expense_claim2.cancel()

		self.assertEqual(frappe.db.get_value("Task", task, "total_expense_claim"), 200)
		self.assertEqual(frappe.db.get_value("Project", project, "total_expense_claim"), 200)

	def test_expense_claim_status_as_payment_from_journal_entry(self):
		# Via Journal Entry
		payable_account = get_payable_account(company_name)
		expense_claim = make_expense_claim(payable_account, 300, 200, company_name, "Travel Expenses - _TC3")

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
		gl_entry = frappe.get_all("GL Entry", {"voucher_type": "Expense Claim", "voucher_no": claim.name})
		self.assertEqual(len(gl_entry), 0)

	def test_expense_claim_status_as_payment_from_payment_entry(self):
		payable_account = get_payable_account(company_name)

		expense_claim = make_expense_claim(payable_account, 300, 200, company_name, "Travel Expenses - _TC3")

		pe = make_claim_payment_entry(expense_claim, 200)

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

		expense_claim1 = make_expense_claim(payable_account, 300, 200, company_name, "Travel Expenses - _TC3")

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
		make_claim_payment_entry(claim, 500)
		claim.reload()

		self.assertEqual(claim.total_amount_reimbursed, 500)
		self.assertEqual(claim.status, "Paid")

	def test_expense_claim_with_deducted_returned_advance(self):
		from hrms.hr.doctype.employee_advance.test_employee_advance import (
			create_return_through_additional_salary,
			get_advances_for_claim,
			make_employee_advance,
			make_journal_entry_for_advance,
		)
		from hrms.hr.doctype.expense_claim.expense_claim import get_allocation_amount
		from hrms.payroll.doctype.salary_component.test_salary_component import create_salary_component
		from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure

		# create employee and employee advance
		employee_name = make_employee("_T@employee.advance", "_Test Company")
		advance = make_employee_advance(employee_name, {"repay_unclaimed_amount_from_salary": 1})
		journal_entry = make_journal_entry_for_advance(advance)
		journal_entry.submit()
		advance.reload()

		# set up salary components and structure
		create_salary_component("Advance Salary - Deduction", type="Deduction")
		make_salary_structure(
			"Test Additional Salary for Advance Return",
			"Monthly",
			employee=employee_name,
			company="_Test Company",
		)

		# create additional salary for advance return
		additional_salary = create_return_through_additional_salary(advance)
		additional_salary.salary_component = "Advance Salary - Deduction"
		additional_salary.payroll_date = nowdate()
		additional_salary.amount = 400
		additional_salary.insert()
		additional_salary.submit()
		advance.reload()

		self.assertEqual(advance.return_amount, 400)

		# create an expense claim
		payable_account = get_payable_account("_Test Company")
		claim = make_expense_claim(
			payable_account, 200, 200, "_Test Company", "Travel Expenses - _TC", do_not_submit=True
		)

		# link advance to the claim
		claim = get_advances_for_claim(claim, advance.name, amount=200)
		claim.save()
		claim.submit()

		# verify the allocation amount
		advance = claim.advances[0]
		self.assertEqual(
			get_allocation_amount(
				unclaimed_amount=advance.unclaimed_amount, return_amount=advance.return_amount
			),
			600,
		)

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
		expense_claim = make_expense_claim(
			payable_account, 300, 200, company_name, "Travel Expenses - _TC3", approval_status="Rejected"
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
		employee = make_employee("test_multi_payment@expenseclaim.com", "_Test Company")
		expense_claim = make_expense_claim(
			payable_account, 5500, 5500, "_Test Company", "Travel Expenses - _TC", employee=employee
		)
		expense_claim.save()
		expense_claim.submit()

		# Payment entry 1: paying 500
		pe1 = make_claim_payment_entry(expense_claim, 500)
		pe1.reload()
		self.assertEqual(pe1.references[0].outstanding_amount, 5000)

		expense_claim.reload()
		outstanding_amount = get_outstanding_amount_for_claim(expense_claim)
		self.assertEqual(outstanding_amount, 5000)
		self.assertEqual(expense_claim.total_amount_reimbursed, 500)

		# Payment entry 2: paying 2000
		pe2 = make_claim_payment_entry(expense_claim, 2000)
		pe2.reload()
		self.assertEqual(pe2.references[0].outstanding_amount, 3000)

		expense_claim.reload()
		outstanding_amount = get_outstanding_amount_for_claim(expense_claim)
		self.assertEqual(outstanding_amount, 3000)
		self.assertEqual(expense_claim.total_amount_reimbursed, 2500)

		# Payment entry 3: paying 3000
		pe3 = make_claim_payment_entry(expense_claim, 3000)
		pe3.reload()
		self.assertEqual(pe3.references[0].outstanding_amount, 0)

		expense_claim.reload()
		outstanding_amount = get_outstanding_amount_for_claim(expense_claim)
		self.assertEqual(outstanding_amount, 0)
		self.assertEqual(expense_claim.total_amount_reimbursed, 5500)

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

		pe = make_claim_payment_entry(expense_claim, 140)

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
			fields=[{"SUM": "debit", "as": "total_debit"}, {"SUM": "credit", "as": "total_credit"}],
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
			fields=[{"SUM": "debit", "as": "total_debit"}, {"SUM": "credit", "as": "total_credit"}],
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
			fields=[{"SUM": "debit", "as": "total_debit"}, {"SUM": "credit", "as": "total_credit"}],
		)
		self.assertEqual(ledger_balance, expected_data)

	def test_company_department_validation(self):
		# validate company and department
		expense_claim = frappe.new_doc("Expense Claim")
		expense_claim.company = "_Test Company 3"
		expense_claim.department = "Accounts - _TC2"
		self.assertRaises(MismatchError, expense_claim.save)

	def test_self_expense_approval(self):
		frappe.db.set_single_value("HR Settings", "prevent_self_expense_approval", 0)

		employee = frappe.get_doc(
			"Employee",
			make_employee("test_self_expense_approval@example.com", "_Test Company"),
		)

		from frappe.utils.user import add_role

		add_role(employee.user_id, "Expense Approver")

		payable_account = get_payable_account("_Test Company")
		expense_claim = make_expense_claim(
			payable_account,
			300,
			200,
			"_Test Company",
			"Travel Expenses - _TC",
			do_not_submit=True,
			employee=employee.name,
		)

		frappe.set_user(employee.user_id)
		expense_claim.submit()

		self.assertEqual(1, expense_claim.docstatus)

	def test_self_expense_approval_not_allowed(self):
		frappe.db.set_single_value("HR Settings", "prevent_self_expense_approval", 1)

		expense_approver = "test_expense_approver@example.com"
		make_employee(expense_approver, company="_Test Company")

		employee = frappe.get_doc(
			"Employee",
			make_employee(
				"test_self_expense_approval@example.com",
				company="_Test Company",
				expense_approver=expense_approver,
			),
		)

		from frappe.utils.user import add_role

		add_role(employee.user_id, "Expense Approver")
		add_role(expense_approver, "Expense Approver")

		payable_account = get_payable_account("_Test Company")
		expense_claim = make_expense_claim(
			payable_account,
			300,
			200,
			"_Test Company",
			"Travel Expenses - _TC",
			do_not_submit=True,
			employee=employee.name,
		)

		expense_claim.expense_approver = expense_approver
		expense_claim.save()

		frappe.set_user(employee.user_id)

		self.assertRaises(frappe.ValidationError, expense_claim.submit)
		expense_claim.reload()

		frappe.set_user(expense_approver)
		expense_claim.submit()

		self.assertEqual(1, expense_claim.docstatus)

	def test_multicurrency_claim(self):
		from hrms.hr.doctype.employee_advance.test_employee_advance import (
			create_advance_account,
			get_advances_for_claim,
			make_employee_advance,
			make_payment_entry,
		)

		advance_account = create_advance_account("Employee Advance (USD)", "USD")
		employee = make_employee(
			"test_adv_in_multicurrency@example.com",
			"_Test Company",
			salary_currency="USD",
			employee_advance_account=advance_account,
		)
		advance = make_employee_advance(employee)
		self.assertEqual(advance.status, "Unpaid")

		payment_entry = make_payment_entry(advance, advance.advance_amount)
		advance.reload()
		self.assertEqual(advance.status, "Paid")
		self.assertEqual(payment_entry.received_amount, advance.paid_amount)

		expected_base_paid = flt(
			advance.paid_amount * payment_entry.transaction_exchange_rate,
			advance.precision("base_paid_amount"),
		)
		self.assertEqual(advance.base_paid_amount, expected_base_paid)
		self.assertEqual(payment_entry.paid_amount, expected_base_paid)

		payable_account = create_account(
			account_name="Payroll Payable (USD)",
			parent_account="Accounts Payable - _TC",
			company="_Test Company",
			account_currency="USD",
			account_type="Payable",
		)
		claim_account = create_account(
			account_name="Travel Expenses (USD)",
			parent_account="Indirect Expenses - _TC",
			company="_Test Company",
			account_currency="USD",
		)
		claim = make_expense_claim(
			payable_account,
			advance.advance_amount,
			advance.advance_amount,
			"_Test Company",
			claim_account,
			args={
				"currency": advance.currency,
				"exchange_rate": get_exchange_rate(
					advance.currency, get_company_currency("_Test Company"), today()
				),
			},
			employee=employee,
			do_not_submit=True,
		)

		claim = get_advances_for_claim(claim, advance.name)
		claim.save().submit()
		claim.reload()
		advance.reload()
		self.assertEqual(claim.status, "Paid")
		self.assertEqual(claim.currency, advance.currency)
		self.assertEqual(advance.status, "Claimed")
		self.assertEqual(claim.total_sanctioned_amount, advance.advance_amount)

		for expense in claim.expenses:
			base_amount = flt(expense.amount * claim.exchange_rate, expense.precision("base_amount"))
			base_sanctioned = flt(
				expense.sanctioned_amount * claim.exchange_rate, expense.precision("base_sanctioned_amount")
			)
			self.assertEqual(expense.base_amount, base_amount)
			self.assertEqual(expense.base_sanctioned_amount, base_sanctioned)

		for claim_advance in claim.advances:
			base_advance_paid = flt(
				claim_advance.advance_paid * claim_advance.exchange_rate,
				claim_advance.precision("base_advance_paid"),
			)
			base_unclaimed_amount = flt(
				claim_advance.unclaimed_amount * claim_advance.exchange_rate,
				claim_advance.precision("base_unclaimed_amount"),
			)
			base_allocated_amount = flt(
				claim_advance.allocated_amount * claim.exchange_rate,
				claim_advance.precision("base_allocated_amount"),
			)
			self.assertEqual(claim_advance.base_advance_paid, base_advance_paid)
			self.assertEqual(claim_advance.base_unclaimed_amount, base_unclaimed_amount)
			self.assertEqual(claim_advance.base_allocated_amount, base_allocated_amount)

		total_base_sanctioned = flt(
			claim.total_sanctioned_amount * claim.exchange_rate,
			claim.precision("base_total_sanctioned_amount"),
		)
		total_advance_amount = flt(
			claim.total_advance_amount * claim.exchange_rate, claim.precision("base_total_advance_amount")
		)
		grand_total = flt(claim.grand_total * claim.exchange_rate, claim.precision("base_grand_total"))
		total_claimed_amount = flt(
			claim.total_claimed_amount * claim.exchange_rate, claim.precision("base_total_claimed_amount")
		)
		self.assertEqual(claim.base_total_sanctioned_amount, total_base_sanctioned)
		self.assertEqual(claim.base_total_advance_amount, total_advance_amount)
		self.assertEqual(claim.base_grand_total, grand_total)
		self.assertEqual(claim.base_total_claimed_amount, total_claimed_amount)
		self.assertEqual(claim.total_exchange_gain_loss, 0)

	def test_advance_claim_multicurrency_gain_loss(self):
		from hrms.hr.doctype.employee_advance.test_employee_advance import (
			create_advance_account,
			get_advances_for_claim,
			make_employee_advance,
			make_payment_entry,
		)

		advance_account = create_advance_account("Employee Advance (USD)", "USD")
		employee = make_employee(
			"test_advance_claim_gain_loss_multicurrency@example.com",
			"_Test Company",
			salary_currency="USD",
			employee_advance_account=advance_account,
		)
		advance = make_employee_advance(employee)
		self.assertEqual(advance.status, "Unpaid")

		make_payment_entry(advance, advance.advance_amount)
		advance.reload()
		self.assertEqual(advance.status, "Paid")

		payable_account = create_account(
			account_name="Payroll Payable (USD)",
			parent_account="Accounts Payable - _TC",
			company="_Test Company",
			account_currency="USD",
			account_type="Payable",
		)
		claim_account = create_account(
			account_name="Travel Expenses (USD)",
			parent_account="Indirect Expenses - _TC",
			company="_Test Company",
			account_currency="USD",
		)
		claim = make_expense_claim(
			payable_account,
			advance.advance_amount,
			advance.advance_amount,
			"_Test Company",
			claim_account,
			args={"currency": advance.currency, "exchange_rate": 65},
			employee=employee,
			do_not_submit=True,
		)

		claim = get_advances_for_claim(claim, advance.name)
		claim.save().submit()
		claim.reload()
		advance.reload()
		self.assertEqual(claim.status, "Paid")
		self.assertEqual(advance.status, "Claimed")

		for claim_advance in claim.advances:
			self.assertEqual(claim_advance.exchange_gain_loss, 2100)
		self.assertEqual(claim.total_exchange_gain_loss, 2100)

		journal = frappe.db.get_value(
			"Journal Entry Account",
			filters={"reference_type": "Expense Claim", "reference_name": claim.name, "docstatus": 1},
			fieldname="parent",
		)
		gain_loss_jv = frappe.get_doc("Journal Entry", journal)
		self.assertEqual(gain_loss_jv.voucher_type, "Exchange Gain Or Loss")
		self.assertEqual(gain_loss_jv.total_debit, 2100)
		self.assertEqual(gain_loss_jv.total_credit, 2100)

	def test_expense_claim_status_as_payment_after_unreconciliation(self):
		from hrms.hr.doctype.employee_advance.test_employee_advance import make_payment_entry

		payable_account = get_payable_account(company_name)

		employee = frappe.db.get_value(
			"Employee",
			{"status": "Active", "company": company_name, "first_name": "test_employee1@expenseclaim.com"},
			"name",
		)
		if not employee:
			employee = make_employee("test_employee1@expenseclaim.com", company=company_name)

		expense_claim = make_expense_claim(payable_account, 300, 200, company_name, "Travel Expenses - _TC3")
		self.assertEqual(expense_claim.docstatus, 1)
		self.assertEqual(expense_claim.status, "Unpaid")

		pe = make_payment_entry(expense_claim, 200)
		expense_claim.reload()
		self.assertEqual(expense_claim.status, "Paid")

		unreconcile_doc = frappe.new_doc("Unreconcile Payment")
		unreconcile_doc.company = company_name
		unreconcile_doc.voucher_type = "Payment Entry"
		unreconcile_doc.voucher_no = pe.name
		unreconcile_doc.append(
			"allocations",
			{
				"account": "Travel Expenses - _TC3",
				"party_type": "Employee",
				"party": employee,
				"reference_doctype": "Expense Claim",
				"reference_name": expense_claim.name,
				"allocated_amount": 200,
				"unlinked": 1,
			},
		)
		unreconcile_doc.insert()
		unreconcile_doc.submit()

		expense_claim.reload()
		self.assertEqual(expense_claim.status, "Unpaid")

	def test_status_on_discard(self):
		payable_account = get_payable_account(company_name)
		expense_claim = make_expense_claim(
			payable_account, 300, 200, company_name, "Travel Expenses - _TC3", do_not_submit=True
		)
		expense_claim.insert()
		expense_claim.reload()
		self.assertEqual(expense_claim.status, "Draft")
		expense_claim.discard()
		expense_claim.reload()
		self.assertEqual(expense_claim.status, "Cancelled")


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
	args=None,
	project=None,
	task_name=None,
	do_not_submit=False,
	taxes=None,
	employee=None,
	approval_status="Approved",
):
	if not employee:
		employee = frappe.db.get_value("Employee", {"status": "Active", "company": company})
		if not employee:
			employee = make_employee("test_employee@expenseclaim.com", company=company)

	currency, cost_center = frappe.db.get_value("Company", company, ["default_currency", "cost_center"])
	expense_claim = {
		"doctype": "Expense Claim",
		"employee": employee,
		"payable_account": payable_account,
		"approval_status": approval_status,
		"company": company,
		"currency": currency,
		"exchange_rate": 1,
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

	if args:
		expense_claim.update(args)
	expense_claim = frappe.get_doc(expense_claim)

	if project:
		expense_claim.project = project
	if task_name:
		expense_claim.task = task_name

	if do_not_submit:
		return expense_claim
	expense_claim.submit()
	return expense_claim


def make_claim_payment_entry(expense_claim, amount):
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
