# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from pypika import Order

import frappe
from frappe import _, msgprint


def execute(filters=None):
	if not filters:
		filters = {}

	advances_list = get_advances(filters)
	columns = get_columns()

	if not advances_list:
		msgprint(_("No record found"))
		return columns, advances_list

	data = []
	for advance in advances_list:
		row = [
			advance.name,
			advance.employee,
			advance.company,
			advance.posting_date,
			advance.advance_amount,
			advance.paid_amount,
			advance.claimed_amount,
			advance.return_amount,
			advance.status,
			advance.currency,
		]
		data.append(row)

	return columns, data


def get_columns():
	return [
		{
			"label": _("Title"),
			"fieldname": "title",
			"fieldtype": "Link",
			"options": "Employee Advance",
			"width": 120,
		},
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
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
			"width": 120,
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
			"width": 120,
		},
		{
			"label": _("Returned Amount"),
			"fieldname": "return_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
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

	query = (
		frappe.qb.from_(EmployeeAdvance)
		.select(
			EmployeeAdvance.name,
			EmployeeAdvance.employee,
			EmployeeAdvance.paid_amount,
			EmployeeAdvance.status,
			EmployeeAdvance.advance_amount,
			EmployeeAdvance.claimed_amount,
			EmployeeAdvance.return_amount,
			EmployeeAdvance.company,
			EmployeeAdvance.posting_date,
			EmployeeAdvance.purpose,
			EmployeeAdvance.currency,
		)
		.where(EmployeeAdvance.docstatus < 2)
	)

	if filters.get("employee"):
		query = query.where(EmployeeAdvance.employee == filters.employee)

	if filters.get("company"):
		query = query.where(EmployeeAdvance.company == filters.company)

	if filters.get("status"):
		query = query.where(EmployeeAdvance.status == filters.status)

	if filters.get("from_date"):
		query = query.where(EmployeeAdvance.posting_date >= filters.from_date)

	if filters.get("to_date"):
		query = query.where(EmployeeAdvance.posting_date <= filters.to_date)

	return query.orderby(EmployeeAdvance.posting_date, EmployeeAdvance.name, order=Order.desc).run(
		as_dict=True
	)
