# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.query_builder.functions import Sum


def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_unclaimed_expese_claims(filters)
	return columns, data


def get_columns():
	return [
		_("Employee") + ":Link/Employee:120",
		_("Employee Name") + "::120",
		_("Expense Claim") + ":Link/Expense Claim:120",
		_("Sanctioned Amount") + ":Currency:120",
		_("Paid Amount") + ":Currency:120",
		_("Outstanding Amount") + ":Currency:150",
	]


def get_unclaimed_expese_claims(filters):
	ec = frappe.qb.DocType("Expense Claim")
	ple = frappe.qb.DocType("Payment Ledger Entry")

	query = (
		frappe.qb.from_(ec)
		.join(ple)
		.on((ec.name == ple.against_voucher_no) & (ple.against_voucher_type == "Expense Claim"))
		.select(
			ec.employee,
			ec.employee_name,
			ec.name,
			ec.total_sanctioned_amount,
			ec.total_amount_reimbursed,
			Sum(ple.amount).as_("outstanding_amt"),
		)
		.where((ec.docstatus == 1) & (ec.is_paid == 0) & (ple.delinked == 0))
		.groupby(ec.name)
		.having(Sum(ple.amount) != 0)
	)

	if filters.get("employee"):
		query = query.where(ec.employee == filters.get("employee"))

	return query.run()
