# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from collections import OrderedDict

import frappe
from frappe import _, msgprint
from frappe.query_builder import Order
from frappe.utils import flt, scrub

import erpnext
from erpnext.setup.utils import get_exchange_rate

AMOUNT_FIELDS = ("advance_amount", "paid_amount", "claimed_amount", "return_amount", "outstanding_amount")


def execute(filters=None):
	if not filters:
		filters = frappe._dict()
	filters = frappe._dict(filters)

	advances_list = get_advances(filters)
	columns = get_columns()

	if not advances_list:
		msgprint(_("No record found"))
		return columns, advances_list

	for advance in advances_list:
		advance.outstanding_amount = advance.paid_amount - (advance.claimed_amount + advance.return_amount)
		advance.department = advance.department or advance.employee_department

	if not filters.get("group_by"):
		for row in advances_list:
			row.title = row.name
			if row.employee_name:
				row.employee = f"{row.employee}: {row.employee_name}"
		return columns, [*advances_list, get_total_row(advances_list, _("Total"))], None, None, None, 1

	grouped = OrderedDict()
	group_labels = OrderedDict()
	for advance in advances_list:
		group_key = advance.get(scrub(filters.get("group_by")))
		grouped.setdefault(group_key, []).append(advance)

		if group_key not in group_labels:
			group_labels[group_key] = (
				f"{advance.employee}: {advance.employee_name}"
				if filters.get("group_by") == "Employee" and advance.employee_name
				else group_key
			) or group_key

	result = []
	for key, rows in grouped.items():
		result.append(get_total_row(rows, group_labels.get(key) or _("Not Set")))

		for row in rows:
			result.append(
				frappe._dict(
					title=row.name,
					employee=f"{row.employee}: {row.employee_name}" if row.employee_name else row.employee,
					advance_account=row.advance_account,
					department=row.department,
					branch=row.branch,
					company=row.company,
					posting_date=row.posting_date,
					advance_amount=row.advance_amount,
					paid_amount=row.paid_amount,
					claimed_amount=row.claimed_amount,
					return_amount=row.return_amount,
					outstanding_amount=row.outstanding_amount,
					status=row.status,
					currency=row.currency,
					indent=1,
				)
			)

	result.append(get_total_row(advances_list, _("Total")))

	return columns, result, None, None, None, 1


def get_total_row(rows, title):
	currencies = {row.currency for row in rows}
	currency = currencies.pop() if len(currencies) == 1 else erpnext.get_company_currency(rows[0].company)

	total = frappe._dict(title=title, currency=currency, bold=1, indent=0)
	for field in AMOUNT_FIELDS:
		total[field] = sum(flt(row.get(field)) * get_conversion_rate(row, currency) for row in rows)
	return total


def get_conversion_rate(row, currency):
	if row.currency == currency:
		return 1
	if flt(row.paid_amount):
		return flt(row.base_paid_amount) / flt(row.paid_amount)
	return flt(get_exchange_rate(row.currency, currency, row.posting_date)) or 1


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
			"fieldtype": "Data",
			"width": 180,
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
			"fieldname": "outstanding_amount",
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
			EmployeeAdvance.base_paid_amount,
		)
		.where(EmployeeAdvance.docstatus < 2)
		.where(
			EmployeeAdvance.name.isin(
				frappe.qb.get_query("Employee Advance", fields=["name"], ignore_permissions=False)
			)
		)
	)

	if filters.get("employee"):
		query = query.where(EmployeeAdvance.employee == filters.get("employee"))

	if filters.get("company"):
		query = query.where(EmployeeAdvance.company == filters.get("company"))

	if filters.get("status"):
		query = query.where(EmployeeAdvance.status == filters.get("status"))

	if filters.get("from_date"):
		query = query.where(EmployeeAdvance.posting_date >= filters.get("from_date"))

	if filters.get("to_date"):
		query = query.where(EmployeeAdvance.posting_date <= filters.get("to_date"))

	if filters.get("department"):
		query = query.where(
			(EmployeeAdvance.department.isin(filters.get("department")))
			| (EmployeeAdvance.department.isnull() & (Employee.department.isin(filters.get("department"))))
		)

	if filters.get("branch"):
		query = query.where(Employee.branch.isin(filters.get("branch")))

	if filters.get("advance_account"):
		query = query.where(EmployeeAdvance.advance_account.isin(filters.get("advance_account")))

	if filters.get("group_by") == "Department":
		query = query.orderby(EmployeeAdvance.department)
	elif filters.get("group_by") == "Branch":
		query = query.orderby(Employee.branch)
	else:
		query = query.orderby(EmployeeAdvance.employee)

	query = query.orderby(EmployeeAdvance.posting_date, order=Order.desc)

	return query.run(as_dict=True)
