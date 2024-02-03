# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)

	return columns, data


def get_columns():
	return [
		{
			"label": _("Leave Ledger Entry"),
			"fieldname": "leave_ledger_entry",
			"fieldtype": "Link",
			"options": "Leave Ledger Entry",
			"hidden": 1,
		},
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 250,
		},
		{
			"label": _("Employee Name"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"hidden": 1,
		},
		{
			"label": _("From Date"),
			"fieldname": "from_date",
			"fieldtype": "Date",
			"width": 120,
		},
		{
			"label": _("To Date"),
			"fieldname": "to_date",
			"fieldtype": "Date",
			"width": 120,
		},
		{
			"label": _("Leaves"),
			"fieldname": "leaves",
			"fieldtype": "Float",
			"width": 80,
		},
		{
			"label": _("Leave Type"),
			"fieldname": "leave_type",
			"fieldtype": "Link",
			"options": "Leave Type",
			"width": 150,
		},
		{
			"label": _("Transaction Type"),
			"fieldname": "transaction_type",
			"fieldtype": "Link",
			"options": "DocType",
			"width": 150,
		},
		{
			"label": _("Transaction Name"),
			"fieldname": "transaction_name",
			"fieldtype": "Dynamic Link",
			"options": "transaction_type",
			"width": 180,
		},
		{
			"label": _("Is Carry Forward"),
			"fieldname": "is_carry_forward",
			"fieldtype": "Check",
			"width": 80,
		},
		{
			"label": _("Is Expired"),
			"fieldname": "is_expired",
			"fieldtype": "Check",
			"width": 80,
		},
		{
			"label": _("Is Leave Without Pay"),
			"fieldname": "is_lwp",
			"fieldtype": "Check",
			"width": 80,
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 150,
		},
		{
			"label": _("Holiday List"),
			"fieldname": "holiday_list",
			"fieldtype": "Link",
			"options": "Holiday List",
			"width": 150,
		},
	]


def get_data(filters):
	Employee = frappe.qb.DocType("Employee")
	Ledger = frappe.qb.DocType("Leave Ledger Entry")

	from_date, to_date = filters.get("from_date"), filters.get("to_date")

	query = (
		frappe.qb.from_(Ledger)
		.inner_join(Employee)
		.on(Ledger.employee == Employee.name)
		.select(
			Ledger.name.as_("leave_ledger_entry"),
			Ledger.employee,
			Ledger.employee_name,
			Ledger.from_date,
			Ledger.to_date,
			Ledger.leave_type,
			Ledger.transaction_type,
			Ledger.transaction_name,
			Ledger.leaves,
			Ledger.is_carry_forward,
			Ledger.is_expired,
			Ledger.is_lwp,
			Ledger.company,
			Ledger.holiday_list,
		)
		.where(
			(Ledger.docstatus == 1)
			& (Ledger.from_date[from_date:to_date])
			& (Ledger.to_date[from_date:to_date])
		)
	)

	if filters.get("employee"):
		query = query.where(Ledger.employee == filters.get("employee"))
	if filters.get("leave_type"):
		query = query.where(Ledger.leave_type == filters.get("leave_type"))
	if filters.get("company"):
		query = query.where(Ledger.company == filters.get("company"))

	if filters.get("department"):
		query = query.where(Employee.department == filters.get("department"))
	if filters.get("status"):
		query = query.where(Employee.status == filters.get("status"))

	query = query.orderby(Ledger.employee, Ledger.leave_type, Ledger.creation)

	return query.run(as_dict=True)
