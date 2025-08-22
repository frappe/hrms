# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.query_builder.functions import Date

Filters = frappe._dict


def execute(filters: Filters = None) -> tuple:
	columns = get_columns()
	data = get_data(filters)

	return columns, data


def get_columns() -> list[dict]:
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
			"width": 240,
		},
		{
			"label": _("Employee Name"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"hidden": 1,
		},
		{
			"label": _("Creation Date"),
			"fieldname": "date",
			"fieldtype": "Date",
			"width": 120,
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
			"fieldtype": "Data",
			"width": 130,
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


def get_data(filters: Filters) -> list[dict]:
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
			Date(Ledger.creation).as_("date"),
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

	for field in ("employee", "leave_type", "company", "transaction_type", "transaction_name"):
		if filters.get(field):
			query = query.where(Ledger[field] == filters.get(field))

	for field in ("department", "status"):
		if filters.get(field):
			query = query.where(Employee[field] == filters.get(field))

	query = query.orderby(Ledger.employee, Ledger.leave_type, Ledger.from_date)
	result = query.run(as_dict=True)

	result = add_total_row(result, filters)

	return result


def add_total_row(result: list[dict], filters: Filters) -> list[dict]:
	add_total_row = False
	leave_type = filters.get("leave_type")

	if filters.get("employee") and filters.get("leave_type"):
		add_total_row = True

	if not add_total_row:
		if not filters.get("employee"):
			# check if all rows have the same employee
			employees_from_result = list(set([row.employee for row in result]))
			if len(employees_from_result) != 1:
				return result

		# check if all rows have the same leave type
		leave_types_from_result = list(set([row.leave_type for row in result]))
		if len(leave_types_from_result) == 1:
			leave_type = leave_types_from_result[0]
			add_total_row = True

	if not add_total_row:
		return result

	total_row = frappe._dict({"employee": _("Total Leaves ({0})").format(leave_type)})
	total_row["leaves"] = sum((row.get("leaves") or 0) for row in result)

	result.append(total_row)
	return result
