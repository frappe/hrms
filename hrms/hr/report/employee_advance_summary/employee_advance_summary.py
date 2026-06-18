# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from collections import OrderedDict

import frappe
from frappe import _, msgprint
from frappe.query_builder import Order
from frappe.utils import scrub


def execute(filters=None):
	if not filters:
		filters = frappe._dict()
	filters = frappe._dict(filters)

	advances_list = get_advances(filters)
	columns = get_columns()

	if not advances_list:
		msgprint(_("No record found"))
		return columns, advances_list

	group_by = filters.group_by
	group_field = scrub(group_by) if group_by else None

	grouped = OrderedDict()
	group_totals = OrderedDict()

	for advance in advances_list:
		advance.balance = advance.paid_amount - (advance.claimed_amount + advance.return_amount)
		advance.department = advance.department or advance.employee_department

		group_key = advance.get(group_field) if group_field else None

		if group_field:
			grouped.setdefault(group_key, []).append(advance)

			if group_key not in group_totals:
				group_totals[group_key] = frappe._dict(
					advance_amount=0,
					paid_amount=0,
					claimed_amount=0,
					return_amount=0,
					balance=0,
					currency=advance.currency,
				)

			group_totals[group_key].advance_amount += advance.advance_amount or 0
			group_totals[group_key].paid_amount += advance.paid_amount or 0
			group_totals[group_key].claimed_amount += advance.claimed_amount or 0
			group_totals[group_key].return_amount += advance.return_amount or 0
			group_totals[group_key].balance += advance.balance

	if not group_field:
		return columns, advances_list

	result = []
	grand_total = frappe._dict(advance_amount=0, paid_amount=0, claimed_amount=0, return_amount=0, balance=0)
	first_currency = None

	for key, rows in grouped.items():
		totals = group_totals[key]

		if not first_currency:
			first_currency = totals.currency

		grand_total.advance_amount += totals.advance_amount
		grand_total.paid_amount += totals.paid_amount
		grand_total.claimed_amount += totals.claimed_amount
		grand_total.return_amount += totals.return_amount
		grand_total.balance += totals.balance

		result.append(
			frappe._dict(
				title=key or _("Not Set"),
				advance_amount=totals.advance_amount,
				paid_amount=totals.paid_amount,
				claimed_amount=totals.claimed_amount,
				return_amount=totals.return_amount,
				balance=totals.balance,
				currency=totals.currency,
				bold=1,
				indent=0,
			)
		)

		for row in rows:
			result.append(
				frappe._dict(
					title=row.name,
					employee=row.employee,
					advance_account=row.advance_account,
					department=row.department,
					branch=row.branch,
					company=row.company,
					posting_date=row.posting_date,
					advance_amount=row.advance_amount,
					paid_amount=row.paid_amount,
					claimed_amount=row.claimed_amount,
					return_amount=row.return_amount,
					balance=row.balance,
					status=row.status,
					currency=row.currency,
					indent=1,
				)
			)

	result.append(
		frappe._dict(
			title=_("Total"),
			advance_amount=grand_total.advance_amount,
			paid_amount=grand_total.paid_amount,
			claimed_amount=grand_total.claimed_amount,
			return_amount=grand_total.return_amount,
			balance=grand_total.balance,
			currency=first_currency,
			bold=1,
			indent=0,
		)
	)

	return columns, result, None, None, None, 1


def get_columns():
	return [
		{
			"label": _("Title"),
			"fieldname": "title",
			"fieldtype": "Link",
			"options": "Employee Advance",
			"width": 160,
		},
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120,
		},
		{
			"label": _("Advance Account"),
			"fieldname": "advance_account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 160,
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
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 120,
		},
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
		{
			"label": _("Advance Amount"),
			"fieldname": "advance_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 130,
		},
		{
			"label": _("Paid Amount"),
			"fieldname": "paid_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"label": _("Claimed Amount"),
			"fieldname": "claimed_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 130,
		},
		{
			"label": _("Returned Amount"),
			"fieldname": "return_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 130,
		},
		{
			"label": _("Outstanding Amount"),
			"fieldname": "balance",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 140,
		},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{
			"label": _("Currency"),
			"fieldtype": "Link",
			"fieldname": "currency",
			"options": "Currency",
			"hidden": 1,
			"width": 120,
		},
	]


def get_advances(filters):
	EmployeeAdvance = frappe.qb.DocType("Employee Advance")
	Employee = frappe.qb.DocType("Employee")

	query = (
		frappe.qb.from_(EmployeeAdvance)
		.left_join(Employee)
		.on(EmployeeAdvance.employee == Employee.name)
		.select(
			EmployeeAdvance.name,
			EmployeeAdvance.employee,
			Employee.employee_name,
			Employee.branch,
			Employee.department.as_("employee_department"),
			EmployeeAdvance.advance_account,
			EmployeeAdvance.department,
			EmployeeAdvance.paid_amount,
			EmployeeAdvance.status,
			EmployeeAdvance.advance_amount,
			EmployeeAdvance.claimed_amount,
			EmployeeAdvance.return_amount,
			EmployeeAdvance.company,
			EmployeeAdvance.posting_date,
			EmployeeAdvance.currency,
		)
		.where(EmployeeAdvance.docstatus < 2)
	)

	if filters.employee:
		query = query.where(EmployeeAdvance.employee == filters.employee)

	if filters.company:
		query = query.where(EmployeeAdvance.company == filters.company)

	if filters.status:
		query = query.where(EmployeeAdvance.status == filters.status)

	if filters.from_date:
		query = query.where(EmployeeAdvance.posting_date >= filters.from_date)

	if filters.to_date:
		query = query.where(EmployeeAdvance.posting_date <= filters.to_date)

	if filters.department:
		query = query.where(
			(EmployeeAdvance.department.isin(filters.department))
			| (EmployeeAdvance.department.isnull() & (Employee.department.isin(filters.department)))
		)

	if filters.branch:
		query = query.where(Employee.branch.isin(filters.branch))

	if filters.advance_account:
		query = query.where(EmployeeAdvance.advance_account.isin(filters.advance_account))

	group_by = filters.group_by
	if group_by == "Department":
		query = query.orderby(EmployeeAdvance.department)
	elif group_by == "Branch":
		query = query.orderby(Employee.branch)
	else:
		query = query.orderby(EmployeeAdvance.employee)

	query = query.orderby(EmployeeAdvance.posting_date, order=Order.desc)

	return query.run(as_dict=True)
