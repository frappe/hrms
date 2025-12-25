# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.functions import Abs, Sum
from frappe.utils import flt, get_link_to_form, nowdate

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
		self.validate_advance_account_currency()
		self.validate_advance_account_type()
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
		self.ignore_linked_doctypes = ("GL Entry", "Payment Ledger Entry", "Advance Payment Ledger Entry")
		self.check_linked_payment_entry()
		self.set_status(update=True)

	def on_update(self):
		self.publish_update()

	def after_delete(self):
		self.publish_update()

	def publish_update(self):
		employee_user = frappe.db.get_value("Employee", self.employee, "user_id", cache=True)
		hrms.refetch_resource("hrms:employee_advance_balance", employee_user)

	def validate_advance_account_type(self):
		account_type = frappe.db.get_value("Account", self.advance_account, "account_type")
		if account_type and (account_type != "Receivable"):
			frappe.throw(
				_("Employee advance account {0} should be of type {1}.").format(
					get_link_to_form("Account", self.advance_account), frappe.bold(_("Receivable"))
				)
			)

	def validate_advance_account_currency(self):
		if self.currency and self.advance_account:
			account_currency = frappe.db.get_value("Account", self.advance_account, "account_currency")
			if self.currency != account_currency:
				frappe.throw(
					_(
						"Advance Account {} currency should be same as Salary Currency of Employee {}. Please select same currency Advance Account"
					).format(frappe.bold(self.advance_account), frappe.bold(self.employee))
				)

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
			elif flt(self.paid_amount) > 0 and (
				flt(self.advance_amount, precision) == flt(self.paid_amount, precision)
				or (self.paid_amount and self.repay_unclaimed_amount_from_salary)
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

	def on_discard(self):
		self.db_set("status", "Cancelled")

	def set_total_advance_paid(self):
		aple = frappe.qb.DocType("Advance Payment Ledger Entry")

		account_type = frappe.get_value("Account", self.advance_account, "account_type")

		if account_type == "Receivable":
			paid_amount_condition = aple.amount > 0
			returned_amount_condition = aple.amount < 0
		elif account_type == "Payable":
			paid_amount_condition = aple.amount < 0
			returned_amount_condition = aple.amount > 0
		else:
			frappe.throw(
				_("Employee advance account {0} should be of type {1}.").format(
					get_link_to_form("Account", self.advance_account),
					frappe.bold(_("Receivable")),
				)
			)

		aple_paid_amount = (
			frappe.qb.from_(aple)
			.select(Abs(Sum(aple.amount)).as_("paid_amount"))
			.select(Abs(Sum(aple.base_amount)).as_("base_paid_amount"))
			.where(
				(aple.company == self.company)
				& (aple.delinked == 0)
				& (aple.against_voucher_type == self.doctype)
				& (aple.against_voucher_no == self.name)
				& (paid_amount_condition)
				& (aple.event == "Submit")
			)
		).run(as_dict=True)[0] or {}
		paid_amount = aple_paid_amount.get("paid_amount") or 0

		return_amount = (
			frappe.qb.from_(aple)
			.select(Abs(Sum(aple.amount)).as_("return_amount"))
			.where(
				(aple.company == self.company)
				& (aple.delinked == 0)
				& (aple.against_voucher_type == self.doctype)
				& (aple.against_voucher_no == self.name)
				& (aple.voucher_type != "Expense Claim")
				& (returned_amount_condition)
			)
		).run(as_dict=True)[0].return_amount or 0

		precision = self.precision("paid_amount")
		paid_amount = flt(paid_amount, precision)
		if paid_amount > flt(self.advance_amount, precision):
			frappe.throw(
				_("Row {0}# Paid Amount cannot be greater than requested advance amount"),
				EmployeeAdvanceOverPayment,
			)

		precision = self.precision("return_amount")
		return_amount = flt(return_amount, precision)

		if return_amount > 0 and return_amount > flt(paid_amount - self.claimed_amount, precision):
			frappe.throw(_("Return amount cannot be greater than unclaimed amount"))

		self.db_set("paid_amount", paid_amount)
		self.db_set("return_amount", return_amount)
		self.set_status(update=True)

		base_paid_amount = aple_paid_amount.get("base_paid_amount") or 0
		self.db_set("base_paid_amount", base_paid_amount)

	def update_claimed_amount(self):
		ec = frappe.qb.DocType("Expense Claim")
		eca = frappe.qb.DocType("Expense Claim Advance")

		claimed_amount = (
			frappe.qb.from_(ec)
			.join(eca)
			.on(ec.name == eca.parent)
			.select(Sum(eca.allocated_amount))
			.where(
				(eca.employee_advance == self.name)
				& (eca.allocated_amount > 0)
				& (ec.approval_status == "Approved")
				& (ec.docstatus == 1)
			)
		).run()[0][0] or 0
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
	payment_account = get_same_currency_bank_cash_account(doc.company, doc.currency, doc.mode_of_payment)

	je = frappe.new_doc("Journal Entry")
	je.posting_date = nowdate()
	je.voucher_type = "Bank Entry"
	je.company = doc.company
	je.remark = "Payment against Employee Advance: " + dn + "\n" + doc.purpose
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

	return je.as_dict()


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
	mode_of_payment=None,
):
	bank_cash_account = get_same_currency_bank_cash_account(company, currency, mode_of_payment)

	advance_account_currency = frappe.db.get_value("Account", advance_account, "account_currency")

	je = frappe.new_doc("Journal Entry")
	je.posting_date = nowdate()
	je.voucher_type = get_voucher_type(mode_of_payment)
	je.company = company
	je.remark = "Return against Employee Advance: " + employee_advance_name
	je.multi_currency = 1 if advance_account_currency != erpnext.get_company_currency(company) else 0

	advance_account_amount = flt(return_amount)

	je.append(
		"accounts",
		{
			"account": advance_account,
			"credit_in_account_currency": advance_account_amount,
			"account_currency": advance_account_currency,
			"reference_type": "Employee Advance",
			"reference_name": employee_advance_name,
			"party_type": "Employee",
			"party": employee,
			"is_advance": "Yes",
			"cost_center": erpnext.get_default_cost_center(company),
		},
	)

	bank_amount = flt(return_amount)
	je.append(
		"accounts",
		{
			"account": bank_cash_account.account or bank_cash_account.name,
			"debit_in_account_currency": bank_amount,
			"account_currency": bank_cash_account.account_currency,
			"account_type": bank_cash_account.account_type,
			"cost_center": erpnext.get_default_cost_center(company),
		},
	)

	return je.as_dict()


def get_same_currency_bank_cash_account(company, currency, mode_of_payment=None):
	company_currency = erpnext.get_company_currency(company)
	if currency == company_currency:
		return get_default_bank_cash_account(company, account_type="Cash", mode_of_payment=mode_of_payment)

	account = None
	if mode_of_payment:
		from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account

		account = get_bank_cash_account(mode_of_payment, company).get("account")

	if not account:
		accounts = frappe.get_all(
			"Account",
			filters={
				"company": company,
				"account_currency": currency,
				"account_type": ["in", ["Cash", "Bank"]],
				"is_group": 0,
			},
			limit=1,
		)
		if not accounts:
			frappe.throw(
				_("No Bank/Cash Account found for currency {0}. Please create one under company {1}.").format(
					frappe.bold(currency), company
				),
				title=_("Account Not Found"),
			)
		account = accounts[0].name
	return frappe.get_cached_value(
		"Account", account, ["name", "account_currency", "account_type"], as_dict=True
	)


def get_voucher_type(mode_of_payment=None):
	voucher_type = "Cash Entry"

	if mode_of_payment:
		mode_of_payment_type = frappe.get_cached_value("Mode of Payment", mode_of_payment, "type")
		if mode_of_payment_type == "Bank":
			voucher_type = "Bank Entry"

	return voucher_type
