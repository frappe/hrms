# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from typing import TYPE_CHECKING, Any

import frappe
from frappe import _
from frappe.utils import add_days, flt

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
	"""
    Update loan repayment amounts on Salary Slip.

    This function ensures that loan amounts included in a Salary Slip are
    calculated based only on the period between `start_date` and `end_date`.
    It prevents duplication by:
      - Calculating cumulative amounts at `end_date`.
      - Subtracting cumulative amounts at (`start_date - 1`).
      - Using the difference as the period-specific payable values.

    Args:
        doc (SalarySlip): The Salary Slip document containing loans and period dates.

    Raises:
        frappe.ValidationError: If repayment amounts entered in the Salary Slip
            exceed the period-specific accrued amounts.
    """
	from lending.loan_management.doctype.loan_repayment.loan_repayment import calculate_amounts

	doc.total_loan_repayment = 0
	doc.total_interest_amount = 0
	doc.total_principal_amount = 0

	if not doc.get("loans", []):
		loan_details = _get_loan_details(doc)

		for loan in loan_details:
			amounts_end = calculate_amounts(loan.name, doc.end_date)

			start_prev_date = add_days(doc.start_date, -1)
			amounts_start = calculate_amounts(loan.name, start_prev_date)

			payable_end = flt(amounts_end.get("payable_amount", 0))
			payable_start = flt(amounts_start.get("payable_amount", 0))

			interest_end = flt(amounts_end.get("interest_amount", 0))
			interest_start = flt(amounts_start.get("interest_amount", 0))

			principal_end = flt(amounts_end.get("payable_principal_amount", 0))
			principal_start = flt(amounts_start.get("payable_principal_amount", 0))

			period_payable = max(0.0, payable_end - payable_start)
			period_interest = max(0.0, interest_end - interest_start)
			period_principal = max(0.0, principal_end - principal_start)

			if period_payable:
				doc.append(
                    "loans",
                    {
                        "loan": loan.name,
                        "total_payment": period_payable,
                        "interest_amount": period_interest,
                        "principal_amount": period_principal,
                        "loan_account": loan.loan_account,
                        "interest_income_account": loan.interest_income_account,
                    },
                )

	if not doc.get("loans"):
		doc.set("loans", [])

	for payment in doc.get("loans", []):
		amounts_end = calculate_amounts(payment.loan, doc.end_date)
		amounts_start = calculate_amounts(payment.loan, add_days(doc.start_date, -1))

		total_period_amount = max(0.0, flt(amounts_end.get("payable_amount", 0)) - flt(amounts_start.get("payable_amount", 0)))

		if payment.total_payment > total_period_amount:
			frappe.throw(
                _(
                    """Row {0}: Paid amount {1} is greater than pending accrued amount {2} against loan {3}"""
                ).format(
                    payment.idx,
                    frappe.bold(payment.total_payment),
                    frappe.bold(total_period_amount),
                    frappe.bold(payment.loan),
                )
            )

		doc.total_interest_amount += flt(payment.interest_amount)
		doc.total_principal_amount += flt(payment.principal_amount)
		doc.total_loan_repayment += flt(payment.total_payment)


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
