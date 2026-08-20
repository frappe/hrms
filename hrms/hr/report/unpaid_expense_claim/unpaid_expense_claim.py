# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from collections import OrderedDict

import frappe
from frappe import _
from frappe.query_builder.functions import Sum

GROUP_BY_FIELD_MAP = {
        "Employee": "employee",
        "Department": "department",
        "Branch": "branch",
}


def execute(filters=None):
	columns = get_columns()
	data = get_unclaimed_expese_claims(filters)

	if not data:
		return columns, data

	if not filters or not filters.get("group_by"):
		return columns, data

	return columns, build_grouped_result(data, filters)


def get_columns():
	return [
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120,
		},
		{
			"label": _("Employee Name"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Expense Claim"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Expense Claim",
			"width": 120,
		},
		{
			"label": _("Posting Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 120,
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 120,
		},
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 120,
		},
		{
			"label": _("Branch"),
			"fieldname": "branch",
			"fieldtype": "Link",
			"options": "Branch",
			"width": 120,
		},
		{
			"label": _("Sanctioned Amount"),
			"fieldname": "total_sanctioned_amount",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Paid Amount"),
			"fieldname": "total_amount_reimbursed",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Outstanding Amount"),
			"fieldname": "outstanding_amt",
			"fieldtype": "Currency",
			"width": 150,
		},
	]


def build_grouped_result(data, filters):
	group_by = filters.get("group_by")
	group_key_field = GROUP_BY_FIELD_MAP.get(group_by)

	if not group_key_field:
		return data
	grouped = OrderedDict()
	group_labels = OrderedDict()
	group_totals = OrderedDict()

	for row in data:
		group_key = row.get(group_key_field)

		grouped.setdefault(group_key, []).append(row)

		if group_key not in group_totals:
			if group_by == "Employee":
				group_labels[group_key] = (
					f"{row.employee}: {row.employee_name}" if row.employee_name else row.employee
				)
			else:
				group_labels[group_key] = group_key

			group_totals[group_key] = frappe._dict(
				total_sanctioned_amount=0,
				total_amount_reimbursed=0,
				outstanding_amt=0,
			)

		group_totals[group_key].total_sanctioned_amount += row.total_sanctioned_amount or 0
		group_totals[group_key].total_amount_reimbursed += row.total_amount_reimbursed or 0
		group_totals[group_key].outstanding_amt += row.outstanding_amt or 0

	result = []
	grand_total = frappe._dict(total_sanctioned_amount=0, total_amount_reimbursed=0, outstanding_amt=0)

	for key, rows in grouped.items():
		totals = group_totals[key]

		grand_total.total_sanctioned_amount += totals.total_sanctioned_amount
		grand_total.total_amount_reimbursed += totals.total_amount_reimbursed
		grand_total.outstanding_amt += totals.outstanding_amt

		result.append(
			frappe._dict(
				employee=group_labels.get(key) or _("Not Set"),
				total_sanctioned_amount=totals.total_sanctioned_amount,
				total_amount_reimbursed=totals.total_amount_reimbursed,
				outstanding_amt=totals.outstanding_amt,
				bold=1,
				indent=0,
			)
		)

		for row in rows:
			result.append(frappe._dict(row, indent=1))

	result.append(
		frappe._dict(
			employee=_("Total"),
			total_sanctioned_amount=grand_total.total_sanctioned_amount,
			total_amount_reimbursed=grand_total.total_amount_reimbursed,
			outstanding_amt=grand_total.outstanding_amt,
			bold=1,
			indent=0,
		)
	)

	return result


def get_unclaimed_expese_claims(filters):
	ec = frappe.qb.DocType("Expense Claim")
	emp = frappe.qb.DocType("Employee")
	ple = frappe.qb.DocType("Payment Ledger Entry")

	query = (
		frappe.qb.from_(ec)
		.join(ple)
		.on((ec.name == ple.against_voucher_no) & (ple.against_voucher_type == "Expense Claim"))
		.left_join(emp)
		.on(ec.employee == emp.name)
		.select(
			ec.employee,
			ec.employee_name,
			ec.name,
			ec.posting_date,
			ec.company,
			ec.department,
			emp.branch,
			ec.total_sanctioned_amount,
			ec.total_amount_reimbursed,
			Sum(ple.amount).as_("outstanding_amt"),
		)
		.where((ec.docstatus == 1) & (ec.is_paid == 0) & (ple.delinked == 0))
		.groupby(ec.name, emp.branch)
		.having(Sum(ple.amount) != 0)
	)

	if filters.get("employee"):
		query = query.where(ec.employee == filters.get("employee"))

	if filters.get("company"):
		query = query.where(ec.company == filters.get("company"))

	if filters.get("department"):
		query = query.where(ec.department == filters.get("department"))

	if filters.get("branch"):
		query = query.where(emp.branch == filters.get("branch"))

	if filters.get("group_by") == "Department":
		query = query.orderby(ec.department)
	elif filters.get("group_by") == "Branch":
		query = query.orderby(emp.branch)
	else:
		query = query.orderby(ec.employee)

	return query.run(as_dict=True)
