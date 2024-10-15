# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from dateutil.relativedelta import relativedelta

import frappe
from frappe.tests.utils import FrappeTestCase, change_settings
from frappe.utils import add_days, add_months

import erpnext
from erpnext.accounts.utils import get_fiscal_year, getdate, nowdate
from erpnext.loan_management.doctype.loan.test_loan import (
	create_loan,
	create_loan_accounts,
	create_loan_type,
	make_loan_disbursement_entry,
)
from erpnext.loan_management.doctype.process_loan_interest_accrual.process_loan_interest_accrual import (
	process_loan_interest_accrual_for_term_loans,
)
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.employee_advance.employee_advance import (
	create_return_through_additional_salary,
)
from hrms.hr.doctype.employee_advance.test_employee_advance import (
	make_employee_advance,
	make_journal_entry_for_advance,
)
from hrms.payroll.doctype.payroll_entry.payroll_entry import (
	PayrollEntry,
	get_end_date,
	get_start_end_dates,
)
from hrms.payroll.doctype.salary_component.test_salary_component import create_salary_component
from hrms.payroll.doctype.salary_slip.test_salary_slip import (
	create_account,
	make_deduction_salary_component,
	make_earning_salary_component,
	mark_attendance,
	set_salary_component_account,
)
from hrms.payroll.doctype.salary_structure.test_salary_structure import (
	create_salary_structure_assignment,
	make_salary_structure,
)
from hrms.tests.test_utils import create_department
from hrms.utils import get_date_range

test_dependencies = ["Holiday List"]


class TestPayrollEntry(FrappeTestCase):
	def setUp(self):
		for dt in [
			"Salary Slip",
			"Salary Component",
			"Salary Component Account",
			"Payroll Entry",
			"Salary Structure",
			"Salary Structure Assignment",
			"Payroll Employee Detail",
			"Additional Salary",
			"Loan",
		]:
			frappe.db.delete(dt)

		make_earning_salary_component(setup=True, company_list=["_Test Company"])
		make_deduction_salary_component(setup=True, test_tax=False, company_list=["_Test Company"])

		frappe.db.set_value("Company", "_Test Company", "default_holiday_list", "_Test Holiday List")
		frappe.db.set_value("Payroll Settings", None, "email_salary_slip_to_employee", 0)

		# set default payable account
		default_account = frappe.db.get_value("Company", "_Test Company", "default_payroll_payable_account")
		if not default_account or default_account != "_Test Payroll Payable - _TC":
			create_account(
				account_name="_Test Payroll Payable",
				company="_Test Company",
				parent_account="Current Liabilities - _TC",
				account_type="Payable",
			)
			frappe.db.set_value(
				"Company", "_Test Company", "default_payroll_payable_account", "_Test Payroll Payable - _TC"
			)

	def test_payroll_entry(self):
		company = frappe.get_doc("Company", "_Test Company")
		employee = frappe.db.get_value("Employee", {"company": "_Test Company"})
		setup_salary_structure(employee, company)

		dates = get_start_end_dates("Monthly", nowdate())
		make_payroll_entry(
			start_date=dates.start_date,
			end_date=dates.end_date,
			payable_account=company.default_payroll_payable_account,
			currency=company.default_currency,
			company=company.name,
		)

	def test_multi_currency_payroll_entry(self):
		company = frappe.get_doc("Company", "_Test Company")
		create_department("Accounts")
		employee = make_employee(
			"test_muti_currency_employee@payroll.com", company=company.name, department="Accounts - _TC"
		)
		salary_structure = "_Test Multi Currency Salary Structure"
		setup_salary_structure(employee, company, "USD", salary_structure)

		dates = get_start_end_dates("Monthly", nowdate())
		payroll_entry = make_payroll_entry(
			start_date=dates.start_date,
			end_date=dates.end_date,
			payable_account=company.default_payroll_payable_account,
			currency="USD",
			exchange_rate=70,
			company=company.name,
			cost_center="Main - _TC",
		)
		payroll_entry.make_payment_entry()

		salary_slip = frappe.db.get_value("Salary Slip", {"payroll_entry": payroll_entry.name}, "name")
		salary_slip = frappe.get_doc("Salary Slip", salary_slip)

		payroll_entry.reload()
		payroll_je = salary_slip.journal_entry
		if payroll_je:
			payroll_je_doc = frappe.get_doc("Journal Entry", payroll_je)
			self.assertEqual(salary_slip.base_gross_pay, payroll_je_doc.total_debit)
			self.assertEqual(salary_slip.base_gross_pay, payroll_je_doc.total_credit)

		payment_entry = frappe.db.sql(
			"""
			select
				ifnull(sum(je.total_debit),0) as total_debit,
				ifnull(sum(je.total_credit),0) as total_credit
			from `tabJournal Entry` je, `tabJournal Entry Account` jea
			where je.name = jea.parent
				and je.voucher_type = 'Bank Entry'
				and jea.reference_name = %s
			""",
			payroll_entry.name,
			as_dict=1,
		)
		self.assertEqual(salary_slip.base_net_pay, payment_entry[0].total_debit)
		self.assertEqual(salary_slip.base_net_pay, payment_entry[0].total_credit)

	@change_settings("Payroll Settings", {"process_payroll_accounting_entry_based_on_employee": 0})
	def test_payroll_entry_with_employee_cost_center(self):
		department = create_department("Cost Center Test")

		employee1 = make_employee(
			"test_emp1@example.com",
			payroll_cost_center="_Test Cost Center - _TC",
			department=department,
			company="_Test Company",
		)
		employee2 = make_employee("test_emp2@example.com", department=department, company="_Test Company")

		create_assignments_with_cost_centers(employee1, employee2)

		dates = get_start_end_dates("Monthly", nowdate())
		pe = make_payroll_entry(
			start_date=dates.start_date,
			end_date=dates.end_date,
			payable_account="_Test Payroll Payable - _TC",
			currency="INR",
			department=department,
			company="_Test Company",
			payment_account="Cash - _TC",
			cost_center="Main - _TC",
		)
		je = frappe.db.get_value("Salary Slip", {"payroll_entry": pe.name}, "journal_entry")
		je_entries = frappe.db.sql(
			"""
			select account, cost_center, debit, credit
			from `tabJournal Entry Account`
			where parent=%s
			order by account, cost_center
		""",
			je,
		)
		expected_je = (
			("_Test Payroll Payable - _TC", "Main - _TC", 0.0, 155600.0),
			("Salary - _TC", "_Test Cost Center - _TC", 124800.0, 0.0),
			("Salary - _TC", "_Test Cost Center 2 - _TC", 31200.0, 0.0),
			("Salary Deductions - _TC", "_Test Cost Center - _TC", 0.0, 320.0),
			("Salary Deductions - _TC", "_Test Cost Center 2 - _TC", 0.0, 80.0),
		)

		self.assertEqual(je_entries, expected_je)

	def test_get_end_date(self):
		self.assertEqual(get_end_date("2017-01-01", "monthly"), {"end_date": "2017-01-31"})
		self.assertEqual(get_end_date("2017-02-01", "monthly"), {"end_date": "2017-02-28"})
		self.assertEqual(get_end_date("2017-02-01", "fortnightly"), {"end_date": "2017-02-14"})
		self.assertEqual(get_end_date("2017-02-01", "bimonthly"), {"end_date": ""})
		self.assertEqual(get_end_date("2017-01-01", "bimonthly"), {"end_date": ""})
		self.assertEqual(get_end_date("2020-02-15", "bimonthly"), {"end_date": ""})
		self.assertEqual(get_end_date("2017-02-15", "monthly"), {"end_date": "2017-03-14"})
		self.assertEqual(get_end_date("2017-02-15", "daily"), {"end_date": "2017-02-15"})

	def test_loan(self):
		company = "_Test Company"
		branch = "Test Employee Branch"

		if not frappe.db.exists("Branch", branch):
			frappe.get_doc({"doctype": "Branch", "branch": branch}).insert()
		holiday_list = make_holiday("test holiday for loan")

		applicant = make_employee(
			"test_employee@loan.com", company="_Test Company", branch=branch, holiday_list=holiday_list
		)
		company_doc = frappe.get_doc("Company", company)

		make_salary_structure(
			"Test Salary Structure for Loan",
			"Monthly",
			employee=applicant,
			company="_Test Company",
			currency=company_doc.default_currency,
		)

		if not frappe.db.exists("Loan Type", "Car Loan"):
			create_loan_accounts()
			create_loan_type(
				"Car Loan",
				500000,
				8.4,
				is_term_loan=1,
				mode_of_payment="Cash",
				disbursement_account="Disbursement Account - _TC",
				payment_account="Payment Account - _TC",
				loan_account="Loan Account - _TC",
				interest_income_account="Interest Income Account - _TC",
				penalty_income_account="Penalty Income Account - _TC",
				repayment_schedule_type="Monthly as per repayment start date",
			)

		loan = create_loan(
			applicant,
			"Car Loan",
			280000,
			"Repay Over Number of Periods",
			20,
			posting_date=add_months(nowdate(), -1),
		)
		loan.repay_from_salary = 1
		loan.submit()

		make_loan_disbursement_entry(loan.name, loan.loan_amount, disbursement_date=add_months(nowdate(), -1))
		process_loan_interest_accrual_for_term_loans(posting_date=nowdate())

		dates = get_start_end_dates("Monthly", nowdate())
		make_payroll_entry(
			company="_Test Company",
			start_date=dates.start_date,
			payable_account=company_doc.default_payroll_payable_account,
			currency=company_doc.default_currency,
			end_date=dates.end_date,
			branch=branch,
			cost_center="Main - _TC",
			payment_account="Cash - _TC",
		)

		name = frappe.db.get_value("Salary Slip", {"posting_date": nowdate(), "employee": applicant}, "name")

		salary_slip = frappe.get_doc("Salary Slip", name)
		for row in salary_slip.loans:
			if row.loan == loan.name:
				interest_amount = (280000 * 8.4) / (12 * 100)
				principal_amount = loan.monthly_repayment_amount - interest_amount
				self.assertEqual(row.interest_amount, interest_amount)
				self.assertEqual(row.principal_amount, principal_amount)
				self.assertEqual(row.total_payment, interest_amount + principal_amount)

	def test_salary_slip_operation_queueing(self):
		company = "_Test Company"
		company_doc = frappe.get_doc("Company", company)
		employee = make_employee("test_employee@payroll.com", company=company)
		setup_salary_structure(employee, company_doc)

		# enqueue salary slip creation via payroll entry
		# Payroll Entry status should change to Queued
		dates = get_start_end_dates("Monthly", nowdate())
		payroll_entry = get_payroll_entry(
			start_date=dates.start_date,
			end_date=dates.end_date,
			payable_account=company_doc.default_payroll_payable_account,
			currency=company_doc.default_currency,
			company=company_doc.name,
			cost_center="Main - _TC",
		)
		frappe.flags.enqueue_payroll_entry = True
		payroll_entry.submit()
		payroll_entry.reload()

		self.assertEqual(payroll_entry.status, "Queued")
		frappe.flags.enqueue_payroll_entry = False

	def test_salary_slip_operation_failure(self):
		company = "_Test Company"
		company_doc = frappe.get_doc("Company", company)
		employee = make_employee("test_employee@payroll.com", company=company)

		salary_structure = make_salary_structure(
			"_Test Salary Structure",
			"Monthly",
			employee,
			company=company,
			currency=company_doc.default_currency,
		)

		# reset account in component to test submission failure
		component = frappe.get_doc("Salary Component", salary_structure.earnings[0].salary_component)
		component.accounts = []
		component.save()

		# salary slip submission via payroll entry
		# Payroll Entry status should change to Failed because of the missing account setup
		dates = get_start_end_dates("Monthly", nowdate())
		payroll_entry = get_payroll_entry(
			start_date=dates.start_date,
			end_date=dates.end_date,
			payable_account=company_doc.default_payroll_payable_account,
			currency=company_doc.default_currency,
			company=company_doc.name,
			cost_center="Main - _TC",
		)

		# set employee as Inactive to check creation failure
		frappe.db.set_value("Employee", employee, "status", "Inactive")
		payroll_entry.submit()
		payroll_entry.reload()
		self.assertEqual(payroll_entry.status, "Failed")
		self.assertIsNotNone(payroll_entry.error_message)

		frappe.db.set_value("Employee", employee, "status", "Active")
		payroll_entry.submit()
		payroll_entry.submit_salary_slips()

		payroll_entry.reload()
		self.assertEqual(payroll_entry.status, "Failed")
		self.assertIsNotNone(payroll_entry.error_message)

		# set accounts
		for data in frappe.get_all("Salary Component", pluck="name"):
			set_salary_component_account(data, company_list=[company])

		# Payroll Entry successful, status should change to Submitted
		payroll_entry.submit_salary_slips()
		payroll_entry.reload()

		self.assertEqual(payroll_entry.status, "Submitted")
		self.assertEqual(payroll_entry.error_message, "")

	def test_payroll_entry_status(self):
		company = "_Test Company"
		company_doc = frappe.get_doc("Company", company)
		employee = make_employee("test_employee@payroll.com", company=company)

		setup_salary_structure(employee, company_doc)

		dates = get_start_end_dates("Monthly", nowdate())
		payroll_entry = get_payroll_entry(
			start_date=dates.start_date,
			end_date=dates.end_date,
			payable_account=company_doc.default_payroll_payable_account,
			currency=company_doc.default_currency,
			company=company_doc.name,
			cost_center="Main - _TC",
		)
		payroll_entry.submit()
		self.assertEqual(payroll_entry.status, "Submitted")

		payroll_entry.cancel()
		self.assertEqual(payroll_entry.status, "Cancelled")

	def test_payroll_entry_cancellation_against_cancelled_journal_entry(self):
		company_doc = frappe.get_doc("Company", "_Test Company")
		employee = make_employee("test_pe_cancellation@payroll.com", company=company_doc.name)

		setup_salary_structure(employee, company_doc)
		dates = get_start_end_dates("Monthly", nowdate())
		payroll_entry = make_payroll_entry(
			start_date=dates.start_date,
			end_date=dates.end_date,
			payable_account=company_doc.default_payroll_payable_account,
			currency=company_doc.default_currency,
			company=company_doc.name,
			cost_center="Main - _TC",
			payment_account="Cash - _TC",
		)
		payroll_entry.reload()
		payroll_entry.make_payment_entry()

		# submit the bank entry journal voucher
		jv = frappe.db.get_value(
			"Journal Entry Account",
			{"reference_type": "Payroll Entry", "reference_name": payroll_entry.name, "docstatus": 0},
			"parent",
		)

		jv_doc = frappe.get_doc("Journal Entry", jv)
		self.assertEqual(jv_doc.accounts[0].cost_center, payroll_entry.cost_center)

		jv_doc.cheque_no = "123456"
		jv_doc.cheque_date = nowdate()
		jv_doc.submit()

		# cancel the salary slip
		salary_slip = frappe.db.get_value("Salary Slip", {"payroll_entry": payroll_entry.name}, "name")
		salary_slip = frappe.get_doc("Salary Slip", salary_slip)
		salary_slip.cancel()

		# cancel the payroll entry
		jvs = frappe.db.get_values(
			"Journal Entry Account",
			{
				"reference_type": "Payroll Entry",
				"reference_name": payroll_entry.name,
			},
			"parent",
			as_dict=True,
		)

		for jv in jvs:
			jv_doc = frappe.get_doc("Journal Entry", jv.parent)
			jv_doc.cancel()

		payroll_entry.cancel()
		self.assertEqual(payroll_entry.status, "Cancelled")

	@change_settings("Payroll Settings", {"process_payroll_accounting_entry_based_on_employee": 1})
	def test_payroll_accrual_journal_entry_with_employee_tagging(self):
		company_doc = frappe.get_doc("Company", "_Test Company")
		employee = make_employee(
			"test_payroll_accrual_journal_entry_with_employee_tagging@payroll.com", company=company_doc.name
		)

		setup_salary_structure(employee, company_doc)

		dates = get_start_end_dates("Monthly", nowdate())
		payroll_entry = make_payroll_entry(
			start_date=dates.start_date,
			end_date=dates.end_date,
			payable_account=company_doc.default_payroll_payable_account,
			currency=company_doc.default_currency,
			company=company_doc.name,
			cost_center="Main - _TC",
		)

		salary_slip = frappe.db.get_value("Salary Slip", {"payroll_entry": payroll_entry.name}, "name")
		salary_slip = frappe.get_doc("Salary Slip", salary_slip)
		payroll_entry.reload()
		payroll_je = salary_slip.journal_entry

		if payroll_je:
			payroll_je_doc = frappe.get_doc("Journal Entry", payroll_je)
			for account in payroll_je_doc.accounts:
				if account.account == company_doc.default_payroll_payable_account:
					self.assertEqual(account.party_type, "Employee")
					self.assertEqual(account.party, employee)

	@change_settings("Payroll Settings", {"process_payroll_accounting_entry_based_on_employee": 0})
	def test_payroll_accrual_journal_entry_without_employee_tagging(self):
		company_doc = frappe.get_doc("Company", "_Test Company")
		employee = make_employee(
			"test_payroll_accrual_journal_entry_without_employee_tagging@payroll.com",
			company=company_doc.name,
		)

		setup_salary_structure(employee, company_doc)

		dates = get_start_end_dates("Monthly", nowdate())
		payroll_entry = make_payroll_entry(
			start_date=dates.start_date,
			end_date=dates.end_date,
			payable_account=company_doc.default_payroll_payable_account,
			currency=company_doc.default_currency,
			company=company_doc.name,
			cost_center="Main - _TC",
		)

		salary_slip = frappe.db.get_value("Salary Slip", {"payroll_entry": payroll_entry.name}, "name")
		salary_slip = frappe.get_doc("Salary Slip", salary_slip)
		payroll_entry.reload()
		payroll_je = salary_slip.journal_entry

		if payroll_je:
			payroll_je_doc = frappe.get_doc("Journal Entry", payroll_je)
			for account in payroll_je_doc.accounts:
				if account.account == company_doc.default_payroll_payable_account:
					self.assertEqual(account.party_type, None)
					self.assertEqual(account.party, None)

	def test_advance_deduction_in_accrual_journal_entry(self):
		company_doc = frappe.get_doc("Company", "_Test Company")
		employee = make_employee("test_employee@payroll.com", company=company_doc.name)

		setup_salary_structure(employee, company_doc)

		# create employee advance
		advance = make_employee_advance(employee, {"repay_unclaimed_amount_from_salary": 1})
		journal_entry = make_journal_entry_for_advance(advance)
		journal_entry.submit()
		advance.reload()

		# return advance through additional salary (deduction)
		component = create_salary_component("Advance Salary - Deduction", **{"type": "Deduction"})
		component.append(
			"accounts",
			{"company": company_doc.name, "account": "Employee Advances - _TC"},
		)
		component.save()

		additional_salary = create_return_through_additional_salary(advance)
		additional_salary.salary_component = component.name
		additional_salary.payroll_date = nowdate()
		additional_salary.amount = advance.paid_amount
		additional_salary.submit()

		# payroll entry
		dates = get_start_end_dates("Monthly", nowdate())
		make_payroll_entry(
			start_date=dates.start_date,
			end_date=dates.end_date,
			payable_account=company_doc.default_payroll_payable_account,
			currency=company_doc.default_currency,
			company=company_doc.name,
			cost_center="Main - _TC",
		)

		# check advance deduction entry correctly mapped in accrual entry
		deduction_entry = frappe.get_all(
			"Journal Entry Account",
			fields=["account", "party", "debit", "credit"],
			filters={
				"reference_type": "Employee Advance",
				"reference_name": advance.name,
				"is_advance": "Yes",
			},
		)[0]

		expected_entry = {
			"account": "Employee Advances - _TC",
			"party": employee,
			"debit": 0.0,
			"credit": advance.paid_amount,
		}

		self.assertEqual(deduction_entry, expected_entry)

	@change_settings("Payroll Settings", {"process_payroll_accounting_entry_based_on_employee": 1})
	def test_employee_wise_bank_entry_with_cost_centers(self):
		department = create_department("Cost Center Test")
		employee1 = make_employee(
			"test_emp1@example.com",
			payroll_cost_center="_Test Cost Center - _TC",
			department=department,
			company="_Test Company",
		)
		employee2 = make_employee("test_emp2@example.com", department=department, company="_Test Company")

		create_assignments_with_cost_centers(employee1, employee2)

		dates = get_start_end_dates("Monthly", nowdate())
		payroll_entry = make_payroll_entry(
			start_date=dates.start_date,
			end_date=dates.end_date,
			payable_account="_Test Payroll Payable - _TC",
			currency="INR",
			department=department,
			company="_Test Company",
			payment_account="Cash - _TC",
			cost_center="Main - _TC",
		)
		payroll_entry.reload()
		payroll_entry.make_payment_entry()

		debit_entries = frappe.db.get_all(
			"Journal Entry Account",
			fields=["party", "account", "cost_center", "debit", "credit"],
			filters={
				"reference_type": "Payroll Entry",
				"reference_name": payroll_entry.name,
				"docstatus": 0,
			},
			order_by="party, cost_center",
		)

		expected_entries = [
			# 100% in a single cost center
			{
				"party": employee1,
				"account": "_Test Payroll Payable - _TC",
				"cost_center": "_Test Cost Center - _TC",
				"debit": 77800.0,
				"credit": 0.0,
			},
			# 60% of 77800.0
			{
				"party": employee2,
				"account": "_Test Payroll Payable - _TC",
				"cost_center": "_Test Cost Center - _TC",
				"debit": 46680.0,
				"credit": 0.0,
			},
			# 40% of 77800.0
			{
				"party": employee2,
				"account": "_Test Payroll Payable - _TC",
				"cost_center": "_Test Cost Center 2 - _TC",
				"debit": 31120.0,
				"credit": 0.0,
			},
		]

		self.assertEqual(debit_entries, expected_entries)

	def test_validate_attendance(self):
		company = frappe.get_doc("Company", "_Test Company")
		employee = frappe.db.get_value("Employee", {"company": "_Test Company"})
		setup_salary_structure(employee, company)

		dates = get_start_end_dates("Monthly", nowdate())
		payroll_entry = get_payroll_entry(
			start_date=dates.start_date,
			end_date=dates.end_date,
			payable_account=company.default_payroll_payable_account,
			currency=company.default_currency,
			company=company.name,
		)

		# case 1: validate unmarked attendance
		payroll_entry.validate_attendance = True
		employees = payroll_entry.get_employees_with_unmarked_attendance()
		self.assertEqual(employees[0]["employee"], employee)

		# case 2: employee should not be flagged for remaining payroll days for a mid-month relieving date
		relieving_date = add_days(payroll_entry.start_date, 15)
		frappe.db.set_value("Employee", employee, "relieving_date", relieving_date)

		for date in get_date_range(payroll_entry.start_date, relieving_date):
			mark_attendance(employee, date, "Present", ignore_validate=True)

		employees = payroll_entry.get_employees_with_unmarked_attendance()
		self.assertFalse(employees)

		# case 3: employee should not flagged for remaining payroll days
		frappe.db.set_value("Employee", employee, "relieving_date", None)

		for date in get_date_range(add_days(relieving_date, 1), payroll_entry.end_date):
			mark_attendance(employee, date, "Present", ignore_validate=True)

		employees = payroll_entry.get_employees_with_unmarked_attendance()
		self.assertFalse(employees)

	@if_lending_app_installed
	@change_settings("Payroll Settings", {"process_payroll_accounting_entry_based_on_employee": 0})
	def test_loan_repayment_from_salary(self):
		from lending.loan_management.doctype.loan.test_loan import make_loan_disbursement_entry
		from lending.loan_management.doctype.process_loan_interest_accrual.process_loan_interest_accrual import (
			process_loan_interest_accrual_for_term_loans,
		)

		frappe.db.delete("Loan")
		applicant, branch, currency, payroll_payable_account = setup_lending()

		loan = create_loan_for_employee(applicant)
		loan_doc = frappe.get_doc("Loan", loan.name)
		loan_doc.repay_from_salary = 1
		loan_doc.save()

		make_loan_disbursement_entry(loan.name, loan.loan_amount, disbursement_date=add_months(nowdate(), -1))
		process_loan_interest_accrual_for_term_loans(posting_date=nowdate())

		dates = get_start_end_dates("Monthly", nowdate())
		payroll_entry = make_payroll_entry(
			company="_Test Company",
			start_date=dates.start_date,
			payable_account=payroll_payable_account,
			currency=currency,
			end_date=dates.end_date,
			branch=branch,
			cost_center="Main - _TC",
			payment_account="Cash - _TC",
			total_loan_repayment=loan.monthly_repayment_amount,
		)

		bank_entry = payroll_entry.make_bank_entry()
		submit_bank_entry(payroll_entry.name)

def get_payroll_entry(**args):
	args = frappe._dict(args)

	payroll_entry: PayrollEntry = frappe.new_doc("Payroll Entry")
	payroll_entry.company = args.company or erpnext.get_default_company()
	payroll_entry.start_date = args.start_date or "2016-11-01"
	payroll_entry.end_date = args.end_date or "2016-11-30"
	payroll_entry.payment_account = get_payment_account()
	payroll_entry.posting_date = nowdate()
	payroll_entry.payroll_frequency = "Monthly"
	payroll_entry.branch = args.branch or None
	payroll_entry.department = args.department or None
	payroll_entry.payroll_payable_account = args.payable_account
	payroll_entry.currency = args.currency
	payroll_entry.exchange_rate = args.exchange_rate or 1

	if args.cost_center:
		payroll_entry.cost_center = args.cost_center

	if args.payment_account:
		payroll_entry.payment_account = args.payment_account

	payroll_entry.fill_employee_details()
	payroll_entry.insert()

	# Commit so that the first salary slip creation failure does not rollback the Payroll Entry insert.
	frappe.db.commit()  # nosemgrep

	return payroll_entry


def make_payroll_entry(**args):
	payroll_entry = get_payroll_entry(**args)
	payroll_entry.submit()
	payroll_entry.submit_salary_slips()
	if payroll_entry.get_sal_slip_list(ss_status=1):
		payroll_entry.make_payment_entry()

	return payroll_entry


def get_payment_account():
	return frappe.get_value(
		"Account",
		{"account_type": "Cash", "company": erpnext.get_default_company(), "is_group": 0},
		"name",
	)


def make_holiday(holiday_list_name):
	if not frappe.db.exists("Holiday List", holiday_list_name):
		current_fiscal_year = get_fiscal_year(nowdate(), as_dict=True)
		dt = getdate(nowdate())

		new_year = dt + relativedelta(month=1, day=1, year=dt.year)
		republic_day = dt + relativedelta(month=1, day=26, year=dt.year)
		test_holiday = dt + relativedelta(month=2, day=2, year=dt.year)

		frappe.get_doc(
			{
				"doctype": "Holiday List",
				"from_date": current_fiscal_year.year_start_date,
				"to_date": current_fiscal_year.year_end_date,
				"holiday_list_name": holiday_list_name,
				"holidays": [
					{"holiday_date": new_year, "description": "New Year"},
					{"holiday_date": republic_day, "description": "Republic Day"},
					{"holiday_date": test_holiday, "description": "Test Holiday"},
				],
			}
		).insert()

	return holiday_list_name


def setup_salary_structure(employee, company_doc, currency=None, salary_structure=None):
	for data in frappe.get_all("Salary Component", pluck="name"):
		if not frappe.db.get_value(
			"Salary Component Account", {"parent": data, "company": company_doc.name}, "name"
		):
			set_salary_component_account(data)

	return make_salary_structure(
		salary_structure or "_Test Salary Structure",
		"Monthly",
		employee,
		company=company_doc.name,
		currency=(currency or company_doc.default_currency),
	)


def create_assignments_with_cost_centers(employee1, employee2):
	company = frappe.get_doc("Company", "_Test Company")
	setup_salary_structure(employee1, company)
	ss = setup_salary_structure(employee2, company, salary_structure="_Test Salary Structure 2")

	# update cost centers in salary structure assignment for employee2
	ssa = frappe.db.get_value(
		"Salary Structure Assignment",
		{"employee": employee2, "salary_structure": ss.name, "docstatus": 1},
		"name",
	)

	ssa_doc = frappe.get_doc("Salary Structure Assignment", ssa)
	ssa_doc.payroll_cost_centers = []
	ssa_doc.append("payroll_cost_centers", {"cost_center": "_Test Cost Center - _TC", "percentage": 60})
	ssa_doc.append("payroll_cost_centers", {"cost_center": "_Test Cost Center 2 - _TC", "percentage": 40})
	ssa_doc.save()
