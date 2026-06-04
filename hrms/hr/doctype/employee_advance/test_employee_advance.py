# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import flt, nowdate

import erpnext
from erpnext.accounts.doctype.account.test_account import create_account
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.employee_advance.employee_advance import (
	EmployeeAdvanceOverPayment,
	create_return_through_additional_salary,
	get_same_currency_bank_cash_account,
	make_return_entry,
)
from hrms.hr.doctype.expense_claim.expense_claim import get_advances, get_expense_claim
from hrms.hr.doctype.expense_claim.test_expense_claim import (
	get_payable_account,
	make_expense_claim,
)
from hrms.payroll.doctype.payroll_entry.payroll_entry import get_start_end_dates
from hrms.payroll.doctype.payroll_entry.test_payroll_entry import make_payroll_entry, setup_salary_structure
from hrms.payroll.doctype.salary_component.test_salary_component import create_salary_component
from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure
from hrms.tests.utils import HRMSTestSuite


class TestEmployeeAdvance(HRMSTestSuite):
	def setUp(self):
		frappe.db.delete("Employee Advance")
		self.update_company_in_fiscal_year()
		frappe.db.set_value("Account", "Employee Advances - _TC", "account_type", "Receivable")
		frappe.db.set_value("Account", "_Test Employee Advance - _TC", "account_type", "Receivable")

	def test_paid_amount_and_status(self):
		employee_name = make_employee("_T@employee.advance", "_Test Company")
		advance = make_employee_advance(employee_name)

		journal_entry = manual_journal_entry_for_advance(advance)
		journal_entry.submit()

		advance.reload()

		self.assertEqual(advance.paid_amount, 1000)
		self.assertEqual(advance.status, "Paid")

		# try making over payment
		journal_entry1 = manual_journal_entry_for_advance(advance)
		self.assertRaises(EmployeeAdvanceOverPayment, journal_entry1.submit)

	def test_paid_amount_on_pe_cancellation(self):
		employee_name = make_employee("_T@employee.advance", "_Test Company")
		advance = make_employee_advance(employee_name)
		payment_entry = make_payment_entry(advance)
		advance.reload()

		self.assertEqual(advance.paid_amount, 1000)
		self.assertEqual(advance.status, "Paid")

		payment_entry.cancel()
		advance.reload()

		self.assertEqual(advance.paid_amount, 0)
		self.assertEqual(advance.status, "Unpaid")

		advance.cancel()
		advance.reload()
		self.assertEqual(advance.status, "Cancelled")

	def test_claimed_status(self):
		# CLAIMED Status check, full amount claimed
		payable_account = get_payable_account("_Test Company")
		claim = make_expense_claim(
			payable_account, 1000, 1000, "_Test Company", "Travel Expenses - _TC", do_not_submit=True
		)

		advance = make_employee_advance(claim.employee)
		make_payment_entry(advance)

		claim = get_advances_for_claim(claim, advance.name)
		claim.save()
		claim.submit()

		advance.reload()
		self.assertEqual(advance.claimed_amount, 1000)
		self.assertEqual(advance.status, "Claimed")

		# advance should not be shown in claims
		advances = get_advances(claim)
		advances = [entry.employee_advance for entry in advances]
		self.assertTrue(advance.name not in advances)

		# cancel claim; status should be Paid
		claim.reload()
		claim.cancel()
		advance.reload()
		self.assertEqual(advance.claimed_amount, 0)
		self.assertEqual(advance.status, "Paid")

	def test_partly_claimed_and_returned_status(self):
		payable_account = get_payable_account("_Test Company")
		claim = make_expense_claim(
			payable_account, 1000, 1000, "_Test Company", "Travel Expenses - _TC", do_not_submit=True
		)

		advance = make_employee_advance(claim.employee)
		make_payment_entry(advance)

		# PARTLY CLAIMED AND RETURNED status check
		# 500 Claimed, 500 Returned
		claim = make_expense_claim(
			payable_account, 500, 500, "_Test Company", "Travel Expenses - _TC", do_not_submit=True
		)

		advance = make_employee_advance(claim.employee)
		make_payment_entry(advance)

		claim = get_advances_for_claim(claim, advance.name, amount=500)
		claim.save()
		claim.submit()

		advance.reload()
		self.assertEqual(advance.claimed_amount, 500)
		self.assertEqual(advance.status, "Paid")

		entry = make_return_entry(
			employee=advance.employee,
			company=advance.company,
			employee_advance_name=advance.name,
			return_amount=flt(advance.paid_amount - advance.claimed_amount),
			advance_account=advance.advance_account,
			mode_of_payment=advance.mode_of_payment,
			currency=advance.currency,
		)

		entry = frappe.get_doc(entry)
		entry.insert()
		entry.submit()

		advance.reload()
		self.assertEqual(advance.return_amount, 500)
		self.assertEqual(advance.status, "Partly Claimed and Returned")

		# advance should not be shown in claims
		advances = get_advances(claim)
		advances = [entry.employee_advance for entry in advances]
		self.assertTrue(advance.name not in advances)

		# Cancel return entry; status should change to PAID
		entry.cancel()
		advance.reload()
		self.assertEqual(advance.return_amount, 0)
		self.assertEqual(advance.status, "Paid")

		# advance should be shown in claims
		advances = get_advances(claim)
		advances = [entry.employee_advance for entry in advances]
		self.assertTrue(advance.name in advances)

	def test_additional_salary_based_advance_repayment_flow(self):
		employee_name = make_employee("_T@employee.advance", "_Test Company")
		advance = make_employee_advance(employee_name, {"repay_unclaimed_amount_from_salary": 1})
		make_payment_entry(advance)

		args = {"type": "Deduction"}
		create_salary_component("Advance Salary - Deduction", **args)
		make_salary_structure(
			"Test Additional Salary for Advance Return",
			"Monthly",
			employee=employee_name,
			company="_Test Company",
		)

		# additional salary for 700 first
		advance.reload()
		additional_salary = create_return_through_additional_salary(advance)
		additional_salary.salary_component = "Advance Salary - Deduction"
		additional_salary.payroll_date = nowdate()
		additional_salary.amount = 700
		additional_salary.insert()
		additional_salary.submit()

		# additional salary for remaining 300
		additional_salary = create_return_through_additional_salary(advance)
		additional_salary.salary_component = "Advance Salary - Deduction"
		additional_salary.payroll_date = nowdate()
		additional_salary.amount = 300
		additional_salary.insert()
		additional_salary.submit()

		# Employee Advance should not be updated directly
		advance.reload()
		self.assertEqual(advance.return_amount, 0)
		self.assertEqual(advance.status, "Paid")

		# should not allow scheduling more than available amount
		additional_salary = create_return_through_additional_salary(advance)
		additional_salary.salary_component = "Advance Salary - Deduction"
		additional_salary.payroll_date = nowdate()
		additional_salary.amount = 100

		self.assertRaises(frappe.ValidationError, additional_salary.insert)

	def test_advance_return_on_payroll_submission(self):
		company_doc = frappe.get_doc("Company", "_Test Company")
		frappe.db.set_value("Account", company_doc.default_payroll_payable_account, "account_type", "Payable")
		employee = make_employee("test_repay_unclaimed_amount@payroll.com", company=company_doc.name)

		setup_salary_structure(employee, company_doc)

		advance = make_employee_advance(
			employee,
			{"repay_unclaimed_amount_from_salary": 1},
		)
		make_payment_entry(advance)
		advance.reload()

		# Advance deduction component
		component = create_salary_component(
			"Advance Salary",
			**{"type": "Deduction"},
		)
		component.append(
			"accounts",
			{
				"company": company_doc.name,
				"account": "Employee Advances - _TC",
			},
		)
		component.save()

		# Create Additional Salary for repayment
		additional_salary = create_return_through_additional_salary(advance)
		additional_salary.salary_component = component.name
		additional_salary.payroll_date = nowdate()
		additional_salary.amount = advance.paid_amount
		additional_salary.submit()

		# Process payroll
		dates = get_start_end_dates("Monthly", nowdate())
		payroll_entry = make_payroll_entry(
			start_date=dates.start_date,
			end_date=dates.end_date,
			payable_account=company_doc.default_payroll_payable_account,
			currency=company_doc.default_currency,
			company=company_doc.name,
			cost_center="Main - _TC",
		)

		salary_slip_name = frappe.db.get_value(
			"Salary Slip",
			{
				"payroll_entry": payroll_entry.name,
				"employee": employee,
			},
			"name",
		)
		self.assertIsNotNone(salary_slip_name)
		salary_slip = frappe.get_doc("Salary Slip", salary_slip_name)

		# Verify advance deduction in salary slip
		deduction_row = next(
			(row for row in salary_slip.deductions if row.salary_component == component.name), None
		)
		self.assertIsNotNone(
			deduction_row,
			"Salary advance deduction not found",
		)
		self.assertEqual(flt(deduction_row.amount), flt(advance.paid_amount))
		self.assertEqual(deduction_row.additional_salary, additional_salary.name)
		advance.reload()
		self.assertEqual(advance.status, "Returned")

	def test_payment_entry_against_advance(self):
		employee_name = make_employee("_T@employee.advance", "_Test Company")
		advance = make_employee_advance(employee_name)

		pe = make_payment_entry(advance, 700)
		advance.reload()
		self.assertEqual(advance.status, "Partially Paid")
		self.assertEqual(advance.paid_amount, 700)

		pe = make_payment_entry(advance, 300)
		advance.reload()
		self.assertEqual(advance.status, "Paid")
		self.assertEqual(advance.paid_amount, 1000)

		pe.cancel()
		advance.reload()
		self.assertEqual(advance.status, "Partially Paid")
		self.assertEqual(advance.paid_amount, 700)

	def test_expense_claim_against_partially_paid_advance(self):
		employee_name = make_employee("_T@employee.advance", "_Test Company")
		advance = make_employee_advance(employee_name)
		make_payment_entry(advance, 700)
		advance.reload()

		self.assertEqual(advance.status, "Partially Paid")

		currency, cost_center = frappe.db.get_value(
			"Company", "_Test Company", ["default_currency", "cost_center"]
		)
		claim = get_expense_claim(advance.name)  # create claim from employee advance form
		claim.update(
			{
				"payable_account": get_payable_account("_Test Company"),
				"currency": currency,
				"exchange_rate": 1,
				"approval_status": "Approved",
			}
		)
		claim.append(
			"expenses",
			{
				"expense_type": "Travel",
				"default_account": "Travel Expenses - _TC",
				"amount": 1000,
				"sanctioned_amount": 1000,
				"cost_center": cost_center,
			},
		)
		claim.save()
		claim.submit()

		self.assertEqual(len(claim.advances), 1)
		self.assertEqual(claim.advances[0].employee_advance, advance.name)
		self.assertEqual(claim.advances[0].advance_paid, 700)
		self.assertEqual(claim.advances[0].allocated_amount, 700)
		self.assertEqual(claim.total_claimed_amount, 1000)
		self.assertEqual(claim.grand_total, 300)

		advance.reload()
		self.assertEqual(advance.claimed_amount, 700)
		self.assertEqual(advance.status, "Claimed")

	def test_precision(self):
		employee_name = make_employee("_T@employee.advance", "_Test Company")
		advance = make_employee_advance(employee_name)
		make_payment_entry(advance)

		# PARTLY CLAIMED AND RETURNED
		payable_account = get_payable_account("_Test Company")
		claim = make_expense_claim(
			payable_account, 650.35, 619.34, "_Test Company", "Travel Expenses - _TC", do_not_submit=True
		)

		claim = get_advances_for_claim(claim, advance.name, amount=619.34)
		claim.save()
		claim.submit()

		advance.reload()
		self.assertEqual(advance.status, "Paid")

		entry = make_return_entry(
			employee=advance.employee,
			company=advance.company,
			employee_advance_name=advance.name,
			return_amount=advance.paid_amount - advance.claimed_amount,
			advance_account=advance.advance_account,
			mode_of_payment=advance.mode_of_payment,
			currency=advance.currency,
		)

		entry = frappe.get_doc(entry)
		entry.insert()
		entry.submit()

		advance.reload()
		# precision is respected
		self.assertEqual(advance.return_amount, 380.66)
		self.assertEqual(advance.status, "Partly Claimed and Returned")

	def test_pending_amount(self):
		employee_name = make_employee("_T@employee.advance", "_Test Company")

		advance1 = make_employee_advance(employee_name)
		make_payment_entry(advance1, 500)
		advance1.reload()
		self.assertEqual(advance1.status, "Partially Paid")

		advance2 = make_employee_advance(employee_name)
		# 1000 - 500
		self.assertEqual(advance2.pending_amount, 500)
		make_payment_entry(advance2, 700)

		advance3 = make_employee_advance(employee_name)
		# (1000 - 500) + (1000 - 700)
		self.assertEqual(advance3.pending_amount, 800)

	@HRMSTestSuite.change_settings(
		"HR Settings", {"unlink_payment_on_cancellation_of_employee_advance": True}
	)
	def test_unlink_payment_entries(self):
		employee_name = make_employee("_T@employee.advance", "_Test Company")
		self.assertTrue(frappe.db.exists("Employee", employee_name))

		advance = make_employee_advance(employee_name)
		self.assertTrue(advance)

		advance_payment = make_payment_entry(advance, 1000)
		self.assertTrue(advance_payment)
		self.assertEqual(advance_payment.total_allocated_amount, 1000)

		advance.reload()
		advance.cancel()
		advance_payment.reload()
		self.assertEqual(advance_payment.unallocated_amount, 1000)
		self.assertEqual(advance_payment.references, [])

	def test_employee_advance_when_different_company_currency(self):
		employee = make_employee("test_adv_in_company_currency@example.com", "_Test Company")

		advance_account = create_advance_account("Employee Advance (USD)", "USD")

		advance = make_employee_advance(
			employee, {"currency": "USD", "exchange_rate": 80, "advance_account": advance_account}
		)
		make_payment_entry(advance, 1000)
		advance.reload()

		self.assertEqual(advance.status, "Paid")
		self.assertEqual(advance.paid_amount, 1000)

	def test_employee_advance_when_different_account_currency(self):
		employee = make_employee("test_adv_in_account_currency@example.com", "_Test Company")
		advance_account = create_advance_account("Employee Advance (USD)", "USD")

		frappe.db.set_value("Company", "_Test Company", "default_employee_advance_account", advance_account)
		advance = make_employee_advance(employee, {"currency": "INR", "exchange_rate": 1})
		make_payment_entry(advance, 1000)
		advance.reload()

		self.assertEqual(advance.status, "Paid")
		self.assertEqual(advance.paid_amount, 1000)

	def test_employee_advance_when_different_advance_currency(self):
		employee = make_employee("test_adv_in_advance_currency@example.com", "_Test Company")
		advance = make_employee_advance(
			employee, {"currency": "USD", "exchange_rate": 80}, do_not_submit=True
		)
		self.assertRaises(frappe.ValidationError, advance.save)

	def update_company_in_fiscal_year(self):
		fy_entries = frappe.get_all("Fiscal Year")
		for fy_entry in fy_entries:
			fiscal_year = frappe.get_doc("Fiscal Year", fy_entry.name)
			company_list = [fy_c.company for fy_c in fiscal_year.companies if fy_c.company]
			if "_Test Company" not in company_list:
				fiscal_year.append("companies", {"company": "_Test Company"})
				fiscal_year.save()

	def test_multicurrency_advance(self):
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

	def test_no_exchange_gain_loss_for_same_currency_advance_payment(self):
		from hrms.overrides.employee_payment_entry import get_payment_entry_for_employee

		gain_loss_account = frappe.db.get_value("Company", "_Test Company", "exchange_gain_loss_account")
		frappe.db.set_value("Company", "_Test Company", "exchange_gain_loss_account", None)

		try:
			employee_name = make_employee("_T@employee.advance", "_Test Company")
			advance = make_employee_advance(employee_name)

			# should not raise error even without exchange_gain_loss_account set at time of payment
			pe = get_payment_entry_for_employee(advance.doctype, advance.name)

			self.assertEqual(flt(pe.source_exchange_rate), 1.0)
			self.assertEqual(flt(pe.target_exchange_rate), 1.0)
			self.assertFalse(any(d.is_exchange_gain_loss for d in pe.deductions))
		finally:
			frappe.db.set_value("Company", "_Test Company", "exchange_gain_loss_account", gain_loss_account)

	def test_status_on_discard(self):
		employee_name = make_employee("Test_status@employee.advance", "_Test Company")
		advance = make_employee_advance(employee_name, do_not_submit=True)
		advance.insert()
		advance.reload()
		self.assertEqual(advance.status, "Draft")
		advance.discard()
		advance.reload()
		self.assertEqual(advance.status, "Cancelled")


def manual_journal_entry_for_advance(advance) -> dict:
	doc = frappe.get_doc("Employee Advance", advance.name)
	payment_account = get_same_currency_bank_cash_account(doc.company, doc.currency, doc.mode_of_payment)

	je = frappe.new_doc("Journal Entry")
	je.posting_date = nowdate()
	je.voucher_type = "Bank Entry"
	je.company = doc.company
	je.remark = "Payment against Employee Advance: " + advance.name + "\n" + doc.purpose
	je.multi_currency = 1 if doc.currency != erpnext.get_company_currency(doc.company) else 0

	je.append(
		"accounts",
		{
			"account": doc.advance_account,
			"account_currency": doc.currency,
			"debit_in_account_currency": flt(doc.advance_amount),
			"reference_type": "Employee Advance",
			"reference_name": doc.name,
			"party_type": "Employee",
			"cost_center": erpnext.get_default_cost_center(doc.company),
			"party": doc.employee,
			"is_advance": "Yes",
		},
	)

	je.append(
		"accounts",
		{
			"account": payment_account.account or payment_account.name,
			"cost_center": erpnext.get_default_cost_center(doc.company),
			"credit_in_account_currency": flt(doc.advance_amount),
			"account_currency": doc.currency,
			"account_type": payment_account.account_type,
		},
	)
	je.cheque_no = "123123"
	je.cheque_date = nowdate()
	je.save()
	return je


def make_payment_entry(advance, amount=None):
	from hrms.overrides.employee_payment_entry import get_payment_entry_for_employee

	payment_entry = get_payment_entry_for_employee(advance.doctype, advance.name, party_amount=amount)

	payment_entry.reference_no = "1"
	payment_entry.reference_date = nowdate()
	payment_entry.submit()
	return payment_entry


def make_employee_advance(employee_name, args=None, do_not_submit=False):
	emp_details = frappe.db.get_value(
		"Employee", employee_name, ["salary_currency", "employee_advance_account"], as_dict=True
	)
	doc = frappe.new_doc("Employee Advance")
	doc.employee = employee_name
	doc.company = "_Test Company"
	doc.purpose = "For site visit"
	doc.currency = emp_details.salary_currency or erpnext.get_company_currency("_Test company")
	doc.advance_amount = 1000
	doc.posting_date = nowdate()
	doc.advance_account = emp_details.employee_advance_account or "_Test Employee Advance - _TC"
	account_type = frappe.db.get_value("Account", "_Test Employee Advance - _TC", "account_type")
	if not account_type:
		frappe.db.set_value("Account", "_Test Employee Advance - _TC", "account_type", "Receivable")

	if args:
		doc.update(args)

	if do_not_submit:
		return doc
	doc.insert()
	doc.submit()
	return doc


def get_advances_for_claim(claim, advance_name, amount=None):
	advances = get_advances(claim, advance_name)
	claim.advances = []
	for advance in advances:
		if amount:
			advance.allocated_amount = amount
		claim.append("advances", advance)
	return claim


def create_advance_account(account_name, account_currency):
	return create_account(
		account_name=account_name,
		parent_account="Accounts Receivable - _TC",
		company="_Test Company",
		account_currency=account_currency,
		account_type="Receivable",
	)
