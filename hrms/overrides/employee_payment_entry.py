# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.utils import flt, nowdate

import erpnext
from erpnext.accounts.doctype.payment_entry.payment_entry import (
	PaymentEntry,
	get_bank_cash_account,
	get_reference_details,
)
from erpnext.accounts.utils import get_account_currency
from erpnext.setup.utils import get_exchange_rate

from hrms.hr.doctype.expense_claim.expense_claim import get_outstanding_amount_for_claim


class EmployeePaymentEntry(PaymentEntry):
	def get_valid_reference_doctypes(self):
		if self.party_type == "Customer":
			return ("Sales Order", "Sales Invoice", "Journal Entry", "Dunning")
		elif self.party_type == "Supplier":
			return ("Purchase Order", "Purchase Invoice", "Journal Entry")
		elif self.party_type == "Shareholder":
			return ("Journal Entry",)
		elif self.party_type == "Employee":
			return ("Expense Claim", "Journal Entry", "Employee Advance", "Gratuity")

	def set_missing_ref_details(
		self,
		force: bool = False,
		update_ref_details_only_for: list | None = None,
		ref_exchange_rate: float | None = None,
	) -> None:
		for d in self.get("references"):
			if d.allocated_amount:
				if update_ref_details_only_for and (
					not (d.reference_doctype, d.reference_name) in update_ref_details_only_for
				):
					continue

				ref_details = get_payment_reference_details(
					d.reference_doctype, d.reference_name, self.party_account_currency
				)

				if ref_exchange_rate:
					ref_details.update({"exchange_rate": ref_exchange_rate})

				for field, value in ref_details.items():
					if d.exchange_gain_loss:
						# for cases where gain/loss is booked into invoice
						# exchange_gain_loss is calculated from invoice & populated
						# and row.exchange_rate is already set to payment entry's exchange rate
						# refer -> `update_reference_in_payment_entry()` in utils.py
						continue

					if field == "exchange_rate" or not d.get(field) or force:
						d.db_set(field, value)


@frappe.whitelist()
def get_payment_entry_for_employee(dt, dn, party_amount=None, bank_account=None, bank_amount=None):
	"""Function to make Payment Entry for Employee Advance, Gratuity, Expense Claim"""
	doc = frappe.get_doc(dt, dn)

	party_type = "Employee"
	party_account = get_party_account(doc)
	party_account_currency = get_account_currency(party_account)
	payment_type = "Pay"
	grand_total, outstanding_amount = get_grand_total_and_outstanding_amount(
		doc, party_amount, party_account_currency
	)

	# bank or cash
	bank = get_bank_cash_account(doc, bank_account)

	paid_amount, received_amount = get_paid_amount_and_received_amount(
		doc, party_account_currency, bank, outstanding_amount, payment_type, bank_amount
	)

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = payment_type
	pe.company = doc.company
	pe.cost_center = doc.get("cost_center")
	pe.posting_date = nowdate()
	pe.mode_of_payment = doc.get("mode_of_payment")
	pe.party_type = "Employee"
	pe.party = doc.get("employee")
	pe.contact_person = doc.get("contact_person")
	pe.contact_email = doc.get("contact_email")
	pe.letter_head = doc.get("letter_head")
	pe.paid_from = bank.account
	pe.paid_to = party_account
	pe.paid_from_account_currency = bank.account_currency
	pe.paid_to_account_currency = party_account_currency
	pe.paid_amount = paid_amount
	pe.received_amount = received_amount

	pe.append(
		"references",
		{
			"reference_doctype": dt,
			"reference_name": dn,
			"bill_no": doc.get("bill_no"),
			"due_date": doc.get("due_date"),
			"total_amount": grand_total,
			"outstanding_amount": outstanding_amount,
			"allocated_amount": outstanding_amount,
		},
	)

	pe.setup_party_account_field()
	pe.set_missing_values()
	pe.set_missing_ref_details()

	if party_account and bank:
		reference_doc = None
		if dt == "Employee Advance":
			reference_doc = doc
		pe.set_exchange_rate(ref_doc=reference_doc)
		pe.set_amounts()

	return pe


def get_party_account(doc):
	party_account = None

	if doc.doctype == "Employee Advance":
		party_account = doc.advance_account
	elif doc.doctype in ("Expense Claim", "Gratuity"):
		party_account = doc.payable_account

	return party_account


def get_grand_total_and_outstanding_amount(doc, party_amount, party_account_currency):
	grand_total = outstanding_amount = 0

	if party_amount:
		grand_total = outstanding_amount = party_amount

	elif doc.doctype == "Expense Claim":
		grand_total = flt(doc.total_sanctioned_amount) + flt(doc.total_taxes_and_charges)
		outstanding_amount = flt(doc.grand_total) - flt(doc.total_amount_reimbursed)

	elif doc.doctype == "Employee Advance":
		grand_total = flt(doc.advance_amount)
		outstanding_amount = flt(doc.advance_amount) - flt(doc.paid_amount)
		if party_account_currency != doc.currency:
			grand_total = flt(doc.advance_amount) * flt(doc.exchange_rate)
			outstanding_amount = (flt(doc.advance_amount) - flt(doc.paid_amount)) * flt(doc.exchange_rate)

	elif doc.doctype == "Gratuity":
		grand_total = doc.amount
		outstanding_amount = flt(doc.amount) - flt(doc.paid_amount)

	else:
		if party_account_currency == doc.company_currency:
			grand_total = flt(doc.get("base_rounded_total") or doc.base_grand_total)
		else:
			grand_total = flt(doc.get("rounded_total") or doc.grand_total)
		outstanding_amount = grand_total - flt(doc.advance_paid)

	return grand_total, outstanding_amount


def get_paid_amount_and_received_amount(
	doc, party_account_currency, bank, outstanding_amount, payment_type, bank_amount
):
	paid_amount = received_amount = 0

	if party_account_currency == bank.account_currency:
		paid_amount = received_amount = abs(outstanding_amount)

	elif payment_type == "Receive":
		paid_amount = abs(outstanding_amount)
		if bank_amount:
			received_amount = bank_amount
		else:
			received_amount = paid_amount * doc.get("conversion_rate", 1)
			if doc.doctype == "Employee Advance":
				received_amount = paid_amount * doc.get("exchange_rate", 1)

	else:
		received_amount = abs(outstanding_amount)
		if bank_amount:
			paid_amount = bank_amount
		else:
			# if party account currency and bank currency is different then populate paid amount as well
			paid_amount = received_amount * doc.get("conversion_rate", 1)
			if doc.doctype == "Employee Advance":
				paid_amount = received_amount * doc.get("exchange_rate", 1)

	return paid_amount, received_amount


@frappe.whitelist()
def get_payment_reference_details(reference_doctype, reference_name, party_account_currency):
	if reference_doctype in ("Expense Claim", "Employee Advance", "Gratuity"):
		return get_reference_details_for_employee(
			reference_doctype, reference_name, party_account_currency
		)
	else:
		return get_reference_details(reference_doctype, reference_name, party_account_currency)


@frappe.whitelist()
def get_reference_details_for_employee(reference_doctype, reference_name, party_account_currency):
	"""
	Returns payment reference details for employee related doctypes:
	Employee Advance, Expense Claim, Gratuity
	"""
	total_amount = outstanding_amount = exchange_rate = None

	ref_doc = frappe.get_doc(reference_doctype, reference_name)
	company_currency = ref_doc.get("company_currency") or erpnext.get_company_currency(
		ref_doc.company
	)

	total_amount, exchange_rate = get_total_amount_and_exchange_rate(
		ref_doc, party_account_currency, company_currency
	)

	if reference_doctype == "Expense Claim":
		outstanding_amount = get_outstanding_amount_for_claim(ref_doc)
	elif reference_doctype == "Employee Advance":
		outstanding_amount = flt(ref_doc.advance_amount) - flt(ref_doc.paid_amount)
		if party_account_currency != ref_doc.currency:
			outstanding_amount = flt(outstanding_amount) * flt(exchange_rate)
	elif reference_doctype == "Gratuity":
		outstanding_amount = ref_doc.amount - flt(ref_doc.paid_amount)
	else:
		outstanding_amount = flt(total_amount) - flt(ref_doc.advance_paid)

	return frappe._dict(
		{
			"due_date": ref_doc.get("due_date"),
			"total_amount": flt(total_amount),
			"outstanding_amount": flt(outstanding_amount),
			"exchange_rate": flt(exchange_rate),
		}
	)


def get_total_amount_and_exchange_rate(ref_doc, party_account_currency, company_currency):
	total_amount = exchange_rate = None

	if ref_doc.doctype == "Expense Claim":
		total_amount = flt(ref_doc.total_sanctioned_amount) + flt(ref_doc.total_taxes_and_charges)
	elif ref_doc.doctype == "Employee Advance":
		total_amount = ref_doc.advance_amount
		exchange_rate = ref_doc.get("exchange_rate")
		if party_account_currency != ref_doc.currency:
			total_amount = flt(total_amount) * flt(exchange_rate)
		if party_account_currency == company_currency:
			exchange_rate = 1

	elif ref_doc.doctype == "Gratuity":
		total_amount = ref_doc.amount

	if not total_amount:
		if party_account_currency == company_currency:
			total_amount = ref_doc.base_grand_total
			exchange_rate = 1
		else:
			total_amount = ref_doc.grand_total

	if not exchange_rate:
		# Get the exchange rate from the original ref doc
		# or get it based on the posting date of the ref doc.
		exchange_rate = ref_doc.get("conversion_rate") or get_exchange_rate(
			party_account_currency, company_currency, ref_doc.posting_date
		)

	return total_amount, exchange_rate
