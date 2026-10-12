# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from itertools import groupby

import frappe
from frappe import _
from frappe.query_builder.functions import Abs, Sum
from frappe.utils import add_days, cint, flt, getdate

from hrms.hr.doctype.leave_allocation.leave_allocation import get_previous_allocation
from hrms.hr.doctype.leave_application.leave_application import (
	get_leave_balance_on,
	get_leaves_for_period,
)

Filters = frappe._dict


def execute(filters: Filters | None = None) -> tuple:
	if filters.to_date <= filters.from_date:
		frappe.throw(_('"From Date" can not be greater than or equal to "To Date"'))

	columns = get_columns()
	data = get_data(filters)
	charts = get_chart_data(data, filters)
	return columns, data, None, charts


def get_columns() -> list[dict]:
	return [
		{
			"label": _("Leave Type"),
			"fieldtype": "Link",
			"fieldname": "leave_type",
			"width": 200,
			"options": "Leave Type",
		},
		{
			"label": _("Employee"),
			"fieldtype": "Link",
			"fieldname": "employee",
			"width": 100,
			"options": "Employee",
		},
		{
			"label": _("Employee Name"),
			"fieldtype": "Dynamic Link",
			"fieldname": "employee_name",
			"width": 100,
			"options": "employee",
		},
		{
			"label": _("Opening Balance"),
			"fieldtype": "float",
			"fieldname": "opening_balance",
			"width": 150,
		},
		{
			"label": _("Leave(s) Allocated"),
			"fieldtype": "float",
			"fieldname": "leaves_allocated",
			"width": 200,
		},
		{
			"label": _("Leave(s) Taken"),
			"fieldtype": "float",
			"fieldname": "leaves_taken",
			"width": 150,
		},
		{
			"label": _("Leave(s) Expired"),
			"fieldtype": "float",
			"fieldname": "leaves_expired",
			"width": 150,
		},
		{
			"label": _("Closing Balance"),
			"fieldtype": "float",
			"fieldname": "closing_balance",
			"width": 150,
		},
	]


def get_data(filters: Filters) -> list:
	leave_types = get_leave_types()
	active_employees = get_employees(filters)
	pairs_with_entries = get_pairs_with_ledger_entries(active_employees, filters.to_date)

	precision = cint(frappe.db.get_single_value("System Settings", "float_precision"))
	consolidate_leave_types = len(active_employees) > 1 and filters.consolidate_leave_types

	data = []

	for leave_type in leave_types:
		rows = []

		for employee in active_employees:
			if (employee.name, leave_type) not in pairs_with_entries:
				continue

			balance = get_balance_details(employee.name, leave_type, filters, precision)
			if not any(balance.values()):
				continue

			row = frappe._dict() if consolidate_leave_types else frappe._dict({"leave_type": leave_type})
			row.update(employee=employee.name, employee_name=employee.employee_name, **balance, indent=1)
			rows.append(row)

		if consolidate_leave_types and rows:
			data.append({"leave_type": leave_type})
		data.extend(rows)

	return data


def get_balance_details(employee: str, leave_type: str, filters: Filters, precision: int) -> dict:
	leaves_taken = get_leaves_for_period(employee, leave_type, filters.from_date, filters.to_date) * -1

	new_allocation, expired_leaves, carry_forwarded_leaves = get_allocated_and_expired_leaves(
		filters.from_date, filters.to_date, employee, leave_type
	)
	on_allocation_boundary = is_opening_balance_on_allocation_boundary(employee, leave_type, filters)
	opening = get_opening_balance(
		employee, leave_type, filters, carry_forwarded_leaves, on_allocation_boundary
	)
	allocated_leaves = new_allocation + carry_forwarded_leaves
	if on_allocation_boundary:
		allocated_leaves -= carry_forwarded_leaves

	leaves_expired = flt(expired_leaves, precision)
	closing = allocated_leaves + opening - (leaves_expired + leaves_taken)

	return {
		"leaves_allocated": flt(allocated_leaves, precision),
		"leaves_expired": leaves_expired,
		"opening_balance": flt(opening, precision),
		"leaves_taken": flt(leaves_taken, precision),
		"closing_balance": flt(closing, precision),
	}


def get_pairs_with_ledger_entries(employees: list[dict], to_date: str) -> set[tuple[str, str]]:
	"""(employee, leave type) pairs with ledger entries up to `to_date`.

	Every balance lookup reads the ledger, so pairs outside this set always balance to zero
	and are left out of the report without running the per-pair queries.
	"""
	if not employees:
		return set()

	Ledger = frappe.qb.DocType("Leave Ledger Entry")
	pairs = (
		frappe.qb.from_(Ledger)
		.select(Ledger.employee, Ledger.leave_type)
		.distinct()
		.where(
			(Ledger.docstatus == 1)
			& (Ledger.from_date <= to_date)
			& (Ledger.employee.isin([employee.name for employee in employees]))
		)
	).run()
	return {tuple(pair) for pair in pairs}


def get_leave_types() -> list[str]:
	LeaveType = frappe.qb.DocType("Leave Type")
	return (frappe.qb.from_(LeaveType).select(LeaveType.name).orderby(LeaveType.name)).run(pluck="name")


def get_employees(filters: Filters) -> list[dict]:
	conditions = {}

	for field in ["company", "department"]:
		if filters.get(field):
			conditions[field] = filters.get(field)

	if filters.get("employee"):
		conditions["name"] = filters.get("employee")

	if filters.get("employee_status"):
		conditions["status"] = filters.get("employee_status")

	return frappe.get_list(
		"Employee",
		filters=conditions,
		fields=["name", "employee_name", "department"],
	)


def get_opening_balance(
	employee: str,
	leave_type: str,
	filters: Filters,
	carry_forwarded_leaves: float,
	on_allocation_boundary: bool,
) -> float:
	# allocation boundary condition
	# opening balance is the closing leave balance 1 day before the filter start date
	opening_balance_date = add_days(filters.from_date, -1)

	if on_allocation_boundary:
		# if opening balance date is same as the previous allocation's expiry
		# then opening balance should only consider carry forwarded leaves
		opening_balance = carry_forwarded_leaves
	else:
		# else directly get leave balance on the previous day
		opening_balance = get_leave_balance_on(employee, leave_type, opening_balance_date)

	return opening_balance


def is_opening_balance_on_allocation_boundary(employee: str, leave_type: str, filters: Filters) -> bool:
	opening_balance_date = add_days(filters.from_date, -1)
	allocation = get_previous_allocation(filters.from_date, leave_type, employee)

	return bool(
		allocation
		and allocation.get("to_date")
		and opening_balance_date
		and getdate(allocation.get("to_date")) == getdate(opening_balance_date)
	)


def get_allocated_and_expired_leaves(
	from_date: str, to_date: str, employee: str, leave_type: str
) -> tuple[float, float, float]:
	new_allocation = 0
	expired_leaves = 0
	carry_forwarded_leaves = 0

	new_allocation = get_allocated_leaves(from_date, to_date, employee, leave_type)
	expired_leaves = get_expired_leaves(from_date, to_date, employee, leave_type)
	carry_forwarded_leaves = get_cf_leaves(from_date, to_date, employee, leave_type)

	return new_allocation, expired_leaves, carry_forwarded_leaves


def get_allocated_leaves(from_date, to_date, employee, leave_type):
	ledger = frappe.qb.DocType("Leave Ledger Entry")
	allocated_leaves = (
		frappe.qb.from_(ledger)
		.select(Sum(ledger.leaves))
		.where(
			(ledger.docstatus == 1)
			& (ledger.transaction_type.isin(["Leave Allocation", "Leave Adjustment"]))
			& (ledger.employee == employee)
			& (ledger.leave_type == leave_type)
			& (ledger.from_date[from_date:to_date])
			& ((ledger.is_expired == 0) & (ledger.is_carry_forward == 0))
		)
	).run()[0][0]
	return allocated_leaves if allocated_leaves else 0.0


def get_expired_leaves(from_date, to_date, employee, leave_type):
	ledger = frappe.qb.DocType("Leave Ledger Entry")
	expired_leaves = (
		frappe.qb.from_(ledger)
		.select(Abs(Sum(ledger.leaves)))
		.where(
			(ledger.docstatus == 1)
			& (ledger.transaction_type == "Leave Allocation")
			& (ledger.employee == employee)
			& (ledger.leave_type == leave_type)
			& ((ledger.from_date[from_date:to_date]) | (ledger.to_date[from_date:to_date]))
			& (ledger.is_expired == 1)
		)
	).run()[0][0]
	return expired_leaves if expired_leaves else 0.0


def get_cf_leaves(from_date, to_date, employee, leave_type):
	ledger = frappe.qb.DocType("Leave Ledger Entry")
	cf_leaves = (
		frappe.qb.from_(ledger)
		.select(Sum(ledger.leaves))
		.where(
			(ledger.docstatus == 1)
			& (ledger.transaction_type == "Leave Allocation")
			& (ledger.employee == employee)
			& (ledger.leave_type == leave_type)
			& (ledger.from_date[from_date:to_date])
			& ((ledger.is_expired == 0) & (ledger.is_carry_forward == 1))
		)
	).run()[0][0]
	return cf_leaves if cf_leaves else 0.0


def get_chart_data(data: list, filters: Filters) -> dict:
	labels = []
	datasets = []
	employee_data = data

	if not data:
		return None

	if data and filters.employee:
		get_dataset_for_chart(employee_data, datasets, labels)

	chart = {
		"data": {"labels": labels, "datasets": datasets},
		"type": "bar",
		"colors": ["#456789", "#EE8888", "#7E77BF"],
	}

	return chart


def get_dataset_for_chart(employee_data: list, datasets: list, labels: list) -> list:
	leaves = []
	employee_data = sorted(employee_data, key=lambda k: k["employee_name"])

	for key, group in groupby(employee_data, lambda x: x["employee_name"]):
		for grp in group:
			if grp.closing_balance:
				leaves.append(
					frappe._dict({"leave_type": grp.leave_type, "closing_balance": grp.closing_balance})
				)

		if leaves:
			labels.append(key)

	for leave in leaves:
		datasets.append({"name": leave.leave_type, "values": [leave.closing_balance]})
