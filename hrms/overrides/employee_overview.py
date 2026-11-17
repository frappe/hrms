import frappe
from frappe import _
from frappe.query_builder import Case, DocType
from frappe.query_builder.functions import Coalesce, Count, Sum
from frappe.utils import add_months, cint, flt, getdate, today

from erpnext.selling.doctype.customer.customer_overview import (
	PERIODS,
	pct_change,
	permitted,
	resolve_period,
)
from erpnext.setup.utils import get_exchange_rate

ATTENDANCE_STATUS = ("Present", "Work From Home", "Half Day", "On Leave", "Absent")
UNPAID_CLAIM_STATUS = ("Unpaid", "Partially Paid")
UNPAID_ADVANCE_STATUS = ("Unpaid", "Partially Paid")
TRANSACTION_TYPES = ("Salary Slip", "Leave Application", "Expense Claim", "Employee Advance")


@frappe.whitelist()
def get_employee_overview(employee: str, period: str = "Current Fiscal Year"):
	company = check_access(employee)

	if period not in PERIODS:
		period = "Current Fiscal Year"

	as_of = getdate(today())
	from_date, to_date = resolve_period(period, company, as_of)

	payload = {
		"employee": employee,
		"company": company,
		"currency": frappe.get_cached_value("Company", company, "default_currency"),
		"period": period,
		"period_range": {"from_date": str(from_date), "to_date": str(to_date)},
		"as_of": str(as_of),
		"permissions": {"payroll": payroll_access()},
		"errors": {},
	}

	for key, fn, args in (
		("pay", pay, (employee, company, from_date, to_date)),
		("attendance", attendance, (employee, from_date, min(to_date, as_of))),
		("leave", leave_balances, (employee, as_of)),
		("pipeline", pipeline, (employee, company, payload["currency"])),
	):
		try:
			payload[key] = fn(*args)
		except Exception:
			payload[key] = None
			payload["errors"][key] = 1
			frappe.log_error(title="Employee Overview: " + key)

	return payload


def check_access(employee):
	if not frappe.has_permission("Employee", "read", doc=employee):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return frappe.db.get_value("Employee", employee, "company")


def payroll_access():
	return bool(frappe.has_permission("Salary Slip", "read"))


def slip_totals(employee, company, from_date, to_date):
	ss = DocType("Salary Slip")
	row = permitted(
		"Salary Slip",
		slip_filters(employee, company, from_date, to_date),
		[
			Coalesce(Sum(ss.base_gross_pay), 0).as_("gross"),
			Coalesce(Sum(ss.base_net_pay), 0).as_("net"),
			Count(ss.name).as_("count"),
		],
	)[0]
	return flt(row.gross), flt(row.net), cint(row.count)


def slip_filters(employee, company, from_date, to_date):
	return [
		["docstatus", "=", 1],
		["employee", "=", employee],
		["company", "=", company],
		["start_date", ">=", from_date],
		["start_date", "<=", to_date],
	]


def pay(employee, company, from_date, to_date):
	if not payroll_access():
		return None

	gross, net, count = slip_totals(employee, company, from_date, to_date)
	prev_gross, prev_net, _count = slip_totals(
		employee, company, add_months(from_date, -12), add_months(to_date, -12)
	)

	ss = DocType("Salary Slip")
	by_month = {}
	for row in permitted(
		"Salary Slip",
		slip_filters(employee, company, from_date, to_date),
		[
			"start_date",
			Sum(ss.base_gross_pay).as_("gross"),
			Sum(ss.base_net_pay).as_("net"),
		],
		group_by="start_date",
	):
		month = getdate(row.start_date).replace(day=1)
		totals = by_month.setdefault(month, [0.0, 0.0])
		totals[0] += flt(row.gross)
		totals[1] += flt(row.net)

	points = []
	cursor = getdate(from_date).replace(day=1)
	while cursor <= getdate(to_date):
		gross_pay, net_pay = by_month.get(cursor, (0.0, 0.0))
		points.append(
			{
				"label": cursor.strftime("%b"),
				"title": cursor.strftime("%b %Y"),
				"gross": gross_pay,
				"net": net_pay,
			}
		)
		cursor = add_months(cursor, 1)

	return {
		"gross": {"value": gross, "count": count, "delta": pct_change(gross, prev_gross)},
		"net": {"value": net, "count": count, "delta": pct_change(net, prev_net)},
		"points": points,
	}


def attendance(employee, from_date, to_date):
	if not frappe.has_permission("Attendance", "read"):
		return None

	att = DocType("Attendance")
	counts = dict.fromkeys(ATTENDANCE_STATUS, 0)
	half_days_absent = 0
	for row in permitted(
		"Attendance",
		[
			["docstatus", "=", 1],
			["employee", "=", employee],
			["attendance_date", ">=", from_date],
			["attendance_date", "<=", to_date],
		],
		["status", "half_day_status", Count(att.name).as_("count")],
		group_by="status, half_day_status",
	):
		if row.status in counts:
			counts[row.status] += cint(row.count)
		if row.status == "Half Day" and row.half_day_status == "Absent":
			half_days_absent += cint(row.count)

	worked = counts["Present"] + counts["Work From Home"] + (counts["Half Day"] - half_days_absent) * 0.5
	working_days = counts["Present"] + counts["Work From Home"] + counts["Half Day"] + counts["Absent"]
	return {
		"counts": counts,
		"marked": sum(counts.values()),
		"days_worked": worked,
		"rate": flt(worked / working_days * 100, 1) if working_days else None,
	}


def leave_balances(employee, as_of):
	if not frappe.has_permission("Leave Allocation", "read"):
		return None

	from hrms.hr.doctype.leave_application.leave_application import get_leave_details

	allocations = get_leave_details(employee, as_of)["leave_allocation"]
	types = [
		{
			"leave_type": leave_type,
			"remaining": flt(details["remaining_leaves"]),
			"total": flt(details["total_leaves"]),
			"taken": flt(details["leaves_taken"]),
			"pending": flt(details["leaves_pending_approval"]),
		}
		for leave_type, details in allocations.items()
	]
	types.sort(key=lambda t: t["remaining"], reverse=True)
	return {
		"types": types,
		"remaining": sum(t["remaining"] for t in types),
		"pending": sum(t["pending"] for t in types),
	}


def pipeline(employee, company, currency):
	tiles = {}
	if frappe.has_permission("Leave Application", "read"):
		tiles["leave_requests"] = open_leave_requests(employee)
	if frappe.has_permission("Expense Claim", "read"):
		tiles.update(claim_tiles(employee, company))
	if frappe.has_permission("Employee Advance", "read"):
		tiles["advances"] = advance_tile(employee, company, currency)
	return tiles


def advance_rate(row, currency):
	if row.currency == currency:
		return 1
	paid = flt(row.paid_amount)
	if paid and flt(row.base_paid_amount):
		return flt(row.base_paid_amount) / paid
	return flt(get_exchange_rate(row.currency, currency, row.posting_date))


def open_leave_requests(employee):
	la = DocType("Leave Application")
	row = permitted(
		"Leave Application",
		{"docstatus": 0, "employee": employee, "status": "Open"},
		[
			Coalesce(Sum(la.total_leave_days), 0).as_("days"),
			Count(la.name).as_("count"),
			Coalesce(Sum(Case().when(la.from_date <= today(), 1).else_(0)), 0).as_("started"),
		],
	)[0]
	return {"value": flt(row.days), "count": cint(row.count), "started": cint(row.started)}


def claim_tiles(employee, company):
	ec = DocType("Expense Claim")
	awaiting = permitted(
		"Expense Claim",
		{"docstatus": 0, "employee": employee, "company": company, "approval_status": "Draft"},
		[
			Coalesce(Sum(ec.total_claimed_amount * ec.exchange_rate), 0).as_("value"),
			Count(ec.name).as_("count"),
		],
	)[0]
	unpaid = permitted(
		"Expense Claim",
		{
			"docstatus": 1,
			"employee": employee,
			"company": company,
			"approval_status": "Approved",
			"status": ["in", UNPAID_CLAIM_STATUS],
		},
		[
			Coalesce(Sum((ec.grand_total - ec.total_amount_reimbursed) * ec.exchange_rate), 0).as_("value"),
			Count(ec.name).as_("count"),
		],
	)[0]
	return {
		"claims_awaiting": {"value": flt(awaiting.value, 2), "count": cint(awaiting.count)},
		"claims_unpaid": {"value": flt(unpaid.value, 2), "count": cint(unpaid.count)},
	}


def advance_tile(employee, company, currency):
	rows = permitted(
		"Employee Advance",
		{"docstatus": 1, "employee": employee, "company": company},
		[
			"name",
			"posting_date",
			"status",
			"currency",
			"advance_amount",
			"paid_amount",
			"base_paid_amount",
			"claimed_amount",
			"return_amount",
		],
	)
	to_settle, to_pay, open_advances = 0.0, 0.0, set()
	for row in rows:
		paid = flt(row.paid_amount)
		rate = advance_rate(row, currency)
		unsettled = paid - flt(row.claimed_amount) - flt(row.return_amount)
		if unsettled > 0:
			to_settle += unsettled * rate
			open_advances.add(row.name)
		if row.status in UNPAID_ADVANCE_STATUS:
			to_pay += (flt(row.advance_amount) - paid) * rate
			open_advances.add(row.name)
	return {"value": flt(to_settle, 2), "to_pay": flt(to_pay, 2), "count": len(open_advances)}


@frappe.whitelist()
def get_employee_transactions(employee: str, doc_type: str = "All", limit: int = 20):
	check_access(employee)

	limit = min(cint(limit) or 20, 100)
	wanted = [doc_type] if doc_type in TRANSACTION_TYPES else list(TRANSACTION_TYPES)

	rows = []
	for doctype in wanted:
		if frappe.has_permission(doctype, "read"):
			rows.extend(transaction_rows(doctype, employee, limit))

	rows.sort(key=lambda r: (r["date"], r["name"]), reverse=True)
	return rows[:limit]


def transaction_rows(doctype, employee, limit):
	fields = {
		"Salary Slip": ["start_date as date", "base_net_pay as amount"],
		"Leave Application": ["from_date as date", "total_leave_days as days", "docstatus"],
		"Expense Claim": [
			"posting_date as date",
			"total_claimed_amount",
			"grand_total",
			"total_amount_reimbursed",
			"exchange_rate",
			"docstatus",
		],
		"Employee Advance": [
			"posting_date as date",
			"currency",
			"advance_amount",
			"paid_amount",
			"claimed_amount",
			"return_amount",
		],
	}[doctype]
	filters = {"employee": employee, "docstatus": ["!=", 2]}
	if doctype in ("Salary Slip", "Employee Advance"):
		filters["docstatus"] = 1

	return [
		{
			"name": r.name,
			"doctype": doctype,
			"type_label": _(doctype),
			"date": str(r.date),
			"status": r.status,
			"amount": row_amount(doctype, r),
			"days": flt(r.days) if doctype == "Leave Application" else None,
			"outstanding": row_outstanding(doctype, r),
			"currency": row_currency(doctype, r),
		}
		for r in frappe.get_list(
			doctype,
			filters=filters,
			fields=["name", "status", "company", *fields],
			order_by="date desc, creation desc",
			limit=limit,
		)
	]


def row_currency(doctype, row):
	if doctype == "Employee Advance":
		return row.currency
	return frappe.get_cached_value("Company", row.company, "default_currency")


def row_amount(doctype, row):
	if doctype == "Employee Advance":
		return flt(row.advance_amount)
	if doctype == "Expense Claim":
		return flt(row.total_claimed_amount) * flt(row.exchange_rate or 1)
	if doctype == "Leave Application":
		return None
	return flt(row.amount)


def row_outstanding(doctype, row):
	if doctype == "Expense Claim" and row.docstatus == 1:
		return (flt(row.grand_total) - flt(row.total_amount_reimbursed)) * flt(row.exchange_rate or 1)
	if doctype == "Employee Advance":
		return flt(row.paid_amount) - flt(row.claimed_amount) - flt(row.return_amount)
	return None


@frappe.whitelist()
def has_activity(employee: str):
	check_access(employee)
	return any(
		frappe.has_permission(doctype, "read")
		and frappe.get_list(doctype, filters={"employee": employee, "docstatus": ["!=", 2]}, limit=1)
		for doctype in (*TRANSACTION_TYPES, "Attendance", "Leave Allocation")
	)
