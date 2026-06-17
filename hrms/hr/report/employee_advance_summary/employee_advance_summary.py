# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from pypika import Order

import frappe
from frappe import _, msgprint

GROUP_BY_FIELDS = {
	"Employee": "employee",
	"Department": "department",
	"Branch": "branch",
}


def execute(filters=None):
	if not filters:
		filters = {}

	advances_list = get_advances(filters)
	columns = get_columns()

	if not advances_list:
		msgprint(_("No record found"))
		return columns, advances_list

	data = []
	group_totals = {}
	groups_seen = []

	group_by = filters.get("group_by")
	group_field = GROUP_BY_FIELDS.get(group_by) if group_by else None

	for advance in advances_list:
		balance = advance.paid_amount - (advance.claimed_amount + advance.return_amount)

		# Resolve department with fallback before computing group key
		advance["department"] = advance.department or advance.employee_department

		group_key = advance.get(group_field) if group_field else None

		if group_field and group_key not in group_totals:
			groups_seen.append(group_key)
			group_totals[group_key] = {
				"advance_amount": 0,
				"paid_amount": 0,
				"claimed_amount": 0,
				"return_amount": 0,
				"balance": 0,
				"currency": advance.currency,
			}

		if group_field:
			group_totals[group_key]["advance_amount"] += advance.advance_amount or 0
			group_totals[group_key]["paid_amount"] += advance.paid_amount or 0
			group_totals[group_key]["claimed_amount"] += advance.claimed_amount or 0
			group_totals[group_key]["return_amount"] += advance.return_amount or 0
			group_totals[group_key]["balance"] += balance

		data.append(
			frappe._dict(
				{
					"title": advance.name,
					"employee": advance.employee,
					"advance_account": advance.advance_account,
					"department": advance.department,
					"branch": advance.branch,
					"company": advance.company,
					"posting_date": advance.posting_date,
					"advance_amount": advance.advance_amount,
					"paid_amount": advance.paid_amount,
					"claimed_amount": advance.claimed_amount,
					"return_amount": advance.return_amount,
					"balance": balance,
					"status": advance.status,
					"currency": advance.currency,
					"_group_key": group_key,
					"indent": 1 if group_field else 0,
				}
			)
		)

	if not group_field:
		return columns, data

	# Build grouped result with subtotal header rows + manual grand total
	group_rows = {}
	for row in data:
		group_rows.setdefault(row["_group_key"], []).append(row)

	result = []
	grand_total = {
		"advance_amount": 0,
		"paid_amount": 0,
		"claimed_amount": 0,
		"return_amount": 0,
		"balance": 0,
	}
	first_currency = None

	for key in groups_seen:
		totals = group_totals[key]
		rows = group_rows.get(key, [])
		if not rows:
			continue

		if not first_currency:
			first_currency = totals["currency"]

		grand_total["advance_amount"] += totals["advance_amount"]
		grand_total["paid_amount"] += totals["paid_amount"]
		grand_total["claimed_amount"] += totals["claimed_amount"]
		grand_total["return_amount"] += totals["return_amount"]
		grand_total["balance"] += totals["balance"]

		result.append(
			frappe._dict(
				{
					"title": key or _("Not Set"),
					"advance_amount": totals["advance_amount"],
					"paid_amount": totals["paid_amount"],
					"claimed_amount": totals["claimed_amount"],
					"return_amount": totals["return_amount"],
					"balance": totals["balance"],
					"currency": totals["currency"],
					"bold": 1,
					"indent": 0,
				}
			)
		)
		result.extend(rows)

	result.append(
		frappe._dict(
			{
				"title": _("Total"),
				"advance_amount": grand_total["advance_amount"],
				"paid_amount": grand_total["paid_amount"],
				"claimed_amount": grand_total["claimed_amount"],
				"return_amount": grand_total["return_amount"],
				"balance": grand_total["balance"],
				"currency": first_currency,
				"bold": 1,
				"indent": 0,
			}
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

	if filters.get("department"):
		departments = filters.get("department")
		query = query.where(
			(EmployeeAdvance.department.isin(departments))
			| (EmployeeAdvance.department.isnull() & (Employee.department.isin(departments)))
		)

	if filters.get("branch"):
		query = query.where(Employee.branch.isin(filters.get("branch")))

	if filters.get("advance_account"):
		query = query.where(EmployeeAdvance.advance_account.isin(filters.get("advance_account")))

	# Order by the group-by field so groups are contiguous
	group_by = filters.get("group_by")
	if group_by == "Department":
		query = query.orderby(EmployeeAdvance.department)
	elif group_by == "Branch":
		query = query.orderby(Employee.branch)
	else:
		query = query.orderby(EmployeeAdvance.employee)

	query = query.orderby(EmployeeAdvance.posting_date, order=Order.desc)

	return query.run(as_dict=True)
