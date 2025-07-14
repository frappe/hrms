# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.functions import Sum
from frappe.utils import flt, nowdate

import erpnext
from erpnext.accounts.doctype.journal_entry.journal_entry import get_default_bank_cash_account

import hrms
from hrms.hr.utils import validate_active_employee


class EmployeeAdvanceOverPayment(frappe.ValidationError):
	pass


class EmployeeAdvance(Document):
	def onload(self):
		self.get("__onload").make_payment_via_journal_entry = frappe.db.get_single_value(
			"Accounts Settings", "make_payment_via_journal_entry"
		)

	def validate(self):
		validate_active_employee(self.employee)
		self.validate_exchange_rate()
		self.set_status()
		self.set_pending_amount()

	def before_submit(self):
		if not self.get("advance_account"):
			default_advance_account = frappe.db.get_value(
				"Company", self.company, "default_employee_advance_account"
			)
			if default_advance_account:
				self.advance_account = default_advance_account
			else:
				frappe.throw(
					_(
						'Advance Account is mandatory. Please set the <a href="/app/company/{0}#default_employee_advance_account" target="_blank">Default Employee Advance Account</a> in the Company record {0} and submit this document.'
					).format(self.company),
					title=_("Missing Advance Account"),
				)

	def on_cancel(self):
		self.ignore_linked_doctypes = ("GL Entry", "Payment Ledger Entry")
		self.check_linked_payment_entry()
		self.set_status(update=True)

	def on_update(self):
		self.publish_update()

	def after_delete(self):
		self.publish_update()

	def publish_update(self):
		employee_user = frappe.db.get_value("Employee", self.employee, "user_id", cache=True)
		hrms.refetch_resource("hrms:employee_advance_balance", employee_user)

	def validate_exchange_rate(self):
		if not self.exchange_rate:
			frappe.throw(_("Exchange Rate cannot be zero."))

	def set_status(self, update=False):
		precision = self.precision("paid_amount")
		total_amount = flt(flt(self.claimed_amount) + flt(self.return_amount), precision)
		status = None

		if self.docstatus == 0:
			status = "Draft"
		elif self.docstatus == 1:
			if flt(self.claimed_amount) > 0 and flt(self.claimed_amount, precision) == flt(
				self.paid_amount, precision
			):
				status = "Claimed"
			elif flt(self.return_amount) > 0 and flt(self.return_amount, precision) == flt(
				self.paid_amount, precision
			):
				status = "Returned"
			elif (
				flt(self.claimed_amount) > 0
				and (flt(self.return_amount) > 0)
				and total_amount == flt(self.paid_amount, precision)
			):
				status = "Partly Claimed and Returned"
			elif flt(self.paid_amount) > 0 and flt(self.advance_amount, precision) == flt(
				self.paid_amount, precision
			):
				status = "Paid"
			else:
				status = "Unpaid"
		elif self.docstatus == 2:
			status = "Cancelled"

		if update:
			self.db_set("status", status)
			self.publish_update()
			self.notify_update()
		else:
			self.status = status

	def set_total_advance_paid(self):
		gle = frappe.qb.DocType("GL Entry")

		paid_amount = (
			frappe.qb.from_(gle)
			.select(Sum(gle.debit).as_("paid_amount"))
			.where(
				(gle.against_voucher_type == "Employee Advance")
				& (gle.against_voucher == self.name)
				& (gle.party_type == "Employee")
				& (gle.party == self.employee)
				& (gle.docstatus == 1)
				& (gle.is_cancelled == 0)
			)
		).run(as_dict=True)[0].paid_amount or 0

		return_amount = (
			frappe.qb.from_(gle)
			.select(Sum(gle.credit).as_("return_amount"))
			.where(
				(gle.against_voucher_type == "Employee Advance")
				& (gle.voucher_type != "Expense Claim")
				& (gle.against_voucher == self.name)
				& (gle.party_type == "Employee")
				& (gle.party == self.employee)
				& (gle.docstatus == 1)
				& (gle.is_cancelled == 0)
			)
		).run(as_dict=True)[0].return_amount or 0

		if paid_amount != 0:
			paid_amount = flt(paid_amount) / flt(self.exchange_rate)
		if return_amount != 0:
			return_amount = flt(return_amount) / flt(self.exchange_rate)

		precision = self.precision("paid_amount")
		paid_amount = flt(paid_amount, precision)
		if paid_amount > flt(self.advance_amount, precision):
			frappe.throw(
				_("Row {0}# Paid Amount cannot be greater than requested advance amount"),
				EmployeeAdvanceOverPayment,
			)

		precision = self.precision("return_amount")
		return_amount = flt(return_amount, precision)

		if return_amount > 0 and return_amount > flt(self.paid_amount - self.claimed_amount, precision):
			frappe.throw(_("Return amount cannot be greater than unclaimed amount"))

		self.db_set("paid_amount", paid_amount)
		self.db_set("return_amount", return_amount)
		self.set_status(update=True)

	def update_claimed_amount(self):
		claimed_amount = (
			frappe.db.sql(
				"""
			SELECT sum(ifnull(allocated_amount, 0))
			FROM `tabExpense Claim Advance` eca, `tabExpense Claim` ec
			WHERE
				eca.employee_advance = %s
				AND ec.approval_status="Approved"
				AND ec.name = eca.parent
				AND ec.docstatus=1
				AND eca.allocated_amount > 0
		""",
				self.name,
			)[0][0]
			or 0
		)

		frappe.db.set_value("Employee Advance", self.name, "claimed_amount", flt(claimed_amount))
		self.reload()
		self.set_status(update=True)

	def set_pending_amount(self):
		Advance = frappe.qb.DocType("Employee Advance")
		self.pending_amount = (
			frappe.qb.from_(Advance)
			.select(Sum(Advance.advance_amount - Advance.paid_amount))
			.where(
				(Advance.employee == self.employee)
				& (Advance.docstatus == 1)
				& (Advance.posting_date <= self.posting_date)
				& (Advance.status == "Unpaid")
			)
		).run()[0][0] or 0.0

	def check_linked_payment_entry(self):
		from erpnext.accounts.utils import (
			remove_ref_doc_link_from_pe,
			update_accounting_ledgers_after_reference_removal,
		)

		if frappe.db.get_single_value("HR Settings", "unlink_payment_on_cancellation_of_employee_advance"):
			remove_ref_doc_link_from_pe(self.doctype, self.name)
			update_accounting_ledgers_after_reference_removal(self.doctype, self.name)


@frappe.whitelist()
def make_bank_entry(dt, dn):
	doc = frappe.get_doc(dt, dn)
	payment_account = get_default_bank_cash_account(
		doc.company, account_type="Cash", mode_of_payment=doc.mode_of_payment
	)
	if not payment_account:
		frappe.throw(_("Please set a Default Cash Account in Company defaults"))

	advance_account_currency = frappe.db.get_value("Account", doc.advance_account, "account_currency")

	advance_amount, advance_exchange_rate = get_advance_amount_advance_exchange_rate(
		advance_account_currency, doc
	)

	paying_amount, paying_exchange_rate = get_paying_amount_paying_exchange_rate(payment_account, doc)

	je = frappe.new_doc("Journal Entry")
	je.posting_date = nowdate()
	je.voucher_type = "Bank Entry"
	je.company = doc.company
	je.remark = "Payment against Employee Advance: " + dn + "\n" + doc.purpose
	je.multi_currency = 1 if advance_account_currency != payment_account.account_currency else 0

	je.append(
		"accounts",
		{
			"account": doc.advance_account,
			"account_currency": advance_account_currency,
			"exchange_rate": flt(advance_exchange_rate),
			"debit_in_account_currency": flt(advance_amount),
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
			"account": payment_account.account,
			"cost_center": erpnext.get_default_cost_center(doc.company),
			"credit_in_account_currency": flt(paying_amount),
			"account_currency": payment_account.account_currency,
			"account_type": payment_account.account_type,
			"exchange_rate": flt(paying_exchange_rate),
		},
	)

	return je.as_dict()


def get_advance_amount_advance_exchange_rate(advance_account_currency, doc):
	if advance_account_currency != doc.currency:
		advance_amount = flt(doc.advance_amount) * flt(doc.exchange_rate)
		advance_exchange_rate = 1
	else:
		advance_amount = doc.advance_amount
		advance_exchange_rate = doc.exchange_rate

	return advance_amount, advance_exchange_rate


def get_paying_amount_paying_exchange_rate(payment_account, doc):
	if payment_account.account_currency != doc.currency:
		paying_amount = flt(doc.advance_amount) * flt(doc.exchange_rate)
		paying_exchange_rate = 1
	else:
		paying_amount = doc.advance_amount
		paying_exchange_rate = doc.exchange_rate

	return paying_amount, paying_exchange_rate


@frappe.whitelist()
def create_return_through_additional_salary(doc):
	import json

	if isinstance(doc, str):
		doc = frappe._dict(json.loads(doc))

	additional_salary = frappe.new_doc("Additional Salary")
	additional_salary.employee = doc.employee
	additional_salary.currency = doc.currency
	additional_salary.overwrite_salary_structure_amount = 0
	additional_salary.amount = doc.paid_amount - doc.claimed_amount
	additional_salary.company = doc.company
	additional_salary.ref_doctype = doc.doctype
	additional_salary.ref_docname = doc.name

	return additional_salary


@frappe.whitelist()
def make_return_entry(
	employee,
	company,
	employee_advance_name,
	return_amount,
	advance_account,
	currency,
	exchange_rate,
	mode_of_payment=None,
):
	bank_cash_account = get_default_bank_cash_account(
		company, account_type="Cash", mode_of_payment=mode_of_payment
	)
	if not bank_cash_account:
		frappe.throw(_("Please set a Default Cash Account in Company defaults"))

	advance_account_currency = frappe.db.get_value("Account", advance_account, "account_currency")

	je = frappe.new_doc("Journal Entry")
	je.posting_date = nowdate()
	je.voucher_type = get_voucher_type(mode_of_payment)
	je.company = company
	je.remark = "Return against Employee Advance: " + employee_advance_name
	je.multi_currency = 1 if advance_account_currency != bank_cash_account.account_currency else 0

	advance_account_amount = (
		flt(return_amount)
		if advance_account_currency == currency
		else flt(return_amount) * flt(exchange_rate)
	)

	je.append(
		"accounts",
		{
			"account": advance_account,
			"credit_in_account_currency": advance_account_amount,
			"account_currency": advance_account_currency,
			"exchange_rate": flt(exchange_rate) if advance_account_currency == currency else 1,
			"reference_type": "Employee Advance",
			"reference_name": employee_advance_name,
			"party_type": "Employee",
			"party": employee,
			"is_advance": "Yes",
			"cost_center": erpnext.get_default_cost_center(company),
		},
	)

	bank_amount = (
		flt(return_amount)
		if bank_cash_account.account_currency == currency
		else flt(return_amount) * flt(exchange_rate)
	)

	je.append(
		"accounts",
		{
			"account": bank_cash_account.account,
			"debit_in_account_currency": bank_amount,
			"account_currency": bank_cash_account.account_currency,
			"account_type": bank_cash_account.account_type,
			"exchange_rate": flt(exchange_rate) if bank_cash_account.account_currency == currency else 1,
			"cost_center": erpnext.get_default_cost_center(company),
		},
	)

	return je.as_dict()


def get_voucher_type(mode_of_payment=None):
	voucher_type = "Cash Entry"

	if mode_of_payment:
		mode_of_payment_type = frappe.get_cached_value("Mode of Payment", mode_of_payment, "type")
		if mode_of_payment_type == "Bank":
			voucher_type = "Bank Entry"

	return voucher_type
