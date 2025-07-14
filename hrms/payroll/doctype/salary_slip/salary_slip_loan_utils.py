# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from typing import TYPE_CHECKING, Any

import frappe
from frappe import _

if TYPE_CHECKING:
	from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip


def if_lending_app_installed(function):
	"""Decorator to check if lending app is installed"""

	def wrapper(*args, **kwargs):
		if "lending" in frappe.get_installed_apps():
			return function(*args, **kwargs)
		return

	return wrapper


@if_lending_app_installed
def set_loan_repayment(doc: "SalarySlip"):
	from lending.loan_management.doctype.loan_repayment.loan_repayment import calculate_amounts

	doc.total_loan_repayment = 0
	doc.total_interest_amount = 0
	doc.total_principal_amount = 0

	if not doc.get("loans", []):
		loan_details = _get_loan_details(doc)

		for loan in loan_details:
			amounts = calculate_amounts(loan.name, doc.end_date)

			if amounts["payable_amount"]:
				doc.append(
					"loans",
					{
						"loan": loan.name,
						"total_payment": amounts["payable_amount"],
						"interest_amount": amounts["interest_amount"],
						"principal_amount": amounts["payable_principal_amount"],
						"loan_account": loan.loan_account,
						"interest_income_account": loan.interest_income_account,
					},
				)
	if not doc.get("loans"):
		doc.set("loans", [])

	for payment in doc.get("loans", []):
		amounts = calculate_amounts(payment.loan, doc.end_date)
		total_amount = amounts["payable_amount"]

		if payment.total_payment > total_amount:
			frappe.throw(
				_(
					"""Row {0}: Paid amount {1} is greater than pending accrued amount {2} against loan {3}"""
				).format(
					payment.idx,
					frappe.bold(payment.total_payment),
					frappe.bold(total_amount),
					frappe.bold(payment.loan),
				)
			)

		doc.total_interest_amount += payment.interest_amount
		doc.total_principal_amount += payment.principal_amount
		doc.total_loan_repayment += payment.total_payment


def _get_loan_details(doc: "SalarySlip") -> dict[str, Any]:
	loan_details = frappe.get_all(
		"Loan",
		fields=["name", "interest_income_account", "loan_account", "loan_product", "is_term_loan"],
		filters={
			"applicant": doc.employee,
			"docstatus": 1,
			"repay_from_salary": 1,
			"company": doc.company,
			"status": ("!=", "Closed"),
		},
	)
	return loan_details


@if_lending_app_installed
def process_loan_interest_accrual_and_demand(doc: "SalarySlip"):
	loans = _get_loan_details(doc)
	if not loans:
		return

	loan_demand_exists = frappe.db.exists("DocType", "Loan Demand")
	if loan_demand_exists:
		from lending.loan_management.doctype.process_loan_demand.process_loan_demand import (
			process_daily_loan_demands,
		)
		from lending.loan_management.doctype.process_loan_interest_accrual.process_loan_interest_accrual import (
			process_loan_interest_accrual_for_loans,
		)
	else:
		from lending.loan_management.doctype.process_loan_interest_accrual.process_loan_interest_accrual import (
			process_loan_interest_accrual_for_term_loans,
		)

	for loan in loans:
		if loan.get("is_term_loan"):
			if loan_demand_exists:
				process_loan_interest_accrual_for_loans(doc.end_date, loan.loan_product, loan.name)
				process_daily_loan_demands(doc.end_date, loan.loan_product, loan.name)
			else:
				process_loan_interest_accrual_for_term_loans(
					posting_date=doc.end_date, loan_product=loan.loan_product, loan=loan.name
				)


@if_lending_app_installed
def make_loan_repayment_entry(doc: "SalarySlip"):
	from lending.loan_management.doctype.loan_repayment.loan_repayment import create_repayment_entry

	payroll_payable_account = get_payroll_payable_account(doc.company, doc.payroll_entry)
	process_payroll_accounting_entry_based_on_employee = frappe.db.get_single_value(
		"Payroll Settings", "process_payroll_accounting_entry_based_on_employee"
	)

	if not doc.get("loans"):
		doc.set("loans", [])

	for loan in doc.get("loans", []):
		if not loan.total_payment:
			continue

		repayment_entry = create_repayment_entry(
			loan.loan,
			doc.employee,
			doc.company,
			doc.posting_date,
			loan.loan_product,
			"Normal Repayment",
			loan.interest_amount,
			loan.principal_amount,
			loan.total_payment,
			payroll_payable_account=payroll_payable_account,
			process_payroll_accounting_entry_based_on_employee=process_payroll_accounting_entry_based_on_employee,
		)

		repayment_entry.save()
		repayment_entry.submit()

		frappe.db.set_value("Salary Slip Loan", loan.name, "loan_repayment_entry", repayment_entry.name)


@if_lending_app_installed
def cancel_loan_repayment_entry(doc: "SalarySlip"):
	if not doc.get("loans"):
		doc.set("loans", [])

	for loan in doc.get("loans", []):
		if loan.loan_repayment_entry:
			repayment_entry = frappe.get_doc("Loan Repayment", loan.loan_repayment_entry)
			repayment_entry.cancel()


def get_payroll_payable_account(company, payroll_entry):
	if payroll_entry:
		payroll_payable_account = frappe.db.get_value(
			"Payroll Entry", payroll_entry, "payroll_payable_account"
		)
	else:
		payroll_payable_account = frappe.db.get_value("Company", company, "default_payroll_payable_account")

	return payroll_payable_account
