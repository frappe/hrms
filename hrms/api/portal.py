"""Aggregating endpoints for the employee portal.

One endpoint per screen. Each returns exactly what the screen renders, so a page
is a single round trip. Field ownership (employee-owned, HR-owned, restricted) is
enforced here, not in the client: restricted fields are never returned.
"""

import frappe
from frappe import _
from frappe.utils import (
	add_days,
	add_months,
	cint,
	flt,
	get_first_day,
	get_last_day,
	getdate,
	nowdate,
)

from hrms.api import get_current_employee, get_current_employee_info
from hrms.api.portal_extensions import nav_items

# Fields the employee maintains themselves.
EMPLOYEE_OWNED = (
	"gender",
	"blood_group",
	"marital_status",
	"personal_email",
	"cell_number",
	"current_address",
	"permanent_address",
	"person_to_be_contacted",
	"relation",
	"emergency_phone_number",
	"bank_name",
	"bank_ac_no",
	"ifsc_code",
)

# Read-only in the portal. Shown at full contrast with a lock, never greyed out.
HR_OWNED = (
	"employee_name",
	"date_of_birth",
	"date_of_joining",
	"designation",
	"department",
	"grade",
	"employment_type",
	"branch",
	"company_email",
	"default_shift",
	"holiday_list",
	"reports_to",
)

# Safe to show any colleague in the directory.
PUBLIC_FIELDS = (
	"name",
	"employee_name",
	"designation",
	"department",
	"branch",
	"company_email",
	"image",
	"reports_to",
	"date_of_joining",
	"status",
	"user_id",
)


def _employee_doc(employee: str | None = None):
	return frappe.get_doc("Employee", employee or get_current_employee())


def _mask(value: str, keep: int = 4) -> str:
	if not value:
		return ""
	value = str(value)
	if len(value) <= keep:
		return value
	return "•" * (len(value) - keep) + value[-keep:]


def _tenure(from_date) -> str:
	if not from_date:
		return ""
	start, today = getdate(from_date), getdate(nowdate())
	months = (today.year - start.year) * 12 + (today.month - start.month)
	if today.day < start.day:
		months -= 1
	months = max(months, 0)
	years, rem = divmod(months, 12)
	if years and rem:
		return f"{years}y {rem}m"
	if years:
		return f"{years}y"
	return f"{rem}m"


@frappe.whitelist()
def get_bootstrap() -> dict:
	"""Identity, nav counts and capability flags. Fetched once on app load."""
	user = frappe.db.get_value("User", frappe.session.user, ["name", "full_name", "user_image"], as_dict=True)
	employee = get_current_employee_info()
	if not employee:
		return {"user": user, "employee": None}

	roles = set(frappe.get_roles())
	is_approver = bool(
		frappe.db.exists("Employee", {"reports_to": employee.name, "status": "Active"})
	) or bool({"HR Manager", "HR User", "Leave Approver", "Expense Approver"} & roles)

	pending_expenses = frappe.db.count(
		"Expense Claim",
		{"employee": employee.name, "docstatus": 0},
	)

	return {
		"user": user,
		"employee": {
			**employee,
			"image": frappe.db.get_value("Employee", employee.name, "image"),
		},
		"is_approver": is_approver,
		# screens contributed by regional/custom apps; none of their code is here
		"extensions": nav_items(),
		"counts": {"expenses": pending_expenses},
		"currency": frappe.db.get_value("Company", employee.company, "default_currency") or "INR",
	}


@frappe.whitelist()
def get_home() -> dict:
	employee = get_current_employee()
	emp = _employee_doc(employee)
	today = getdate(nowdate())

	# --- check-in state -------------------------------------------------
	last_log = frappe.db.get_value(
		"Employee Checkin",
		{"employee": employee},
		["name", "time", "log_type"],
		order_by="time desc",
		as_dict=True,
	)
	checked_in = bool(last_log and last_log.log_type == "IN")
	shift = None
	if emp.default_shift:
		shift = frappe.db.get_value(
			"Shift Type", emp.default_shift, ["name", "start_time", "end_time"], as_dict=True
		)

	# --- attendance for the current week --------------------------------
	week_start = add_days(today, -today.weekday())
	week_rows = frappe.get_all(
		"Attendance",
		filters={
			"employee": employee,
			"docstatus": 1,
			"attendance_date": ["between", [week_start, add_days(week_start, 6)]],
		},
		fields=["attendance_date", "status", "working_hours"],
	)
	week_map = {str(r.attendance_date): r for r in week_rows}
	week = []
	for i in range(7):
		day = add_days(week_start, i)
		row = week_map.get(str(day))
		week.append(
			{
				"date": str(day),
				"label": getdate(day).strftime("%a"),
				"status": row.status if row else None,
				"hours": flt(row.working_hours, 1) if row else None,
				"is_today": getdate(day) == today,
			}
		)

	# --- my recent requests, cross doctype -------------------------------
	requests = _recent_requests(employee, limit=5)

	# --- waiting on you ---------------------------------------------------
	pending = _pending_approvals(employee)

	# --- who is out today -------------------------------------------------
	out_today = _out_today(emp.company, employee)

	# --- coming up ---------------------------------------------------------
	coming_up = _coming_up(emp)

	return {
		"greeting_name": (emp.first_name or emp.employee_name or "").split(" ")[0],
		"today": str(today),
		"checkin": {
			"checked_in": checked_in,
			"since": str(last_log.time) if checked_in and last_log else None,
			"last_log_type": last_log.log_type if last_log else None,
			"shift": shift,
			"enabled": bool(
				frappe.db.get_single_value("HR Settings", "allow_employee_checkin_from_mobile_app")
			),
		},
		"week": week,
		"requests": requests,
		"pending_approvals": pending,
		"out_today": out_today,
		"coming_up": coming_up,
	}


def _leave_balances(employee: str) -> list[dict]:
	"""Allocation against leaves taken, for the current allocation period."""
	from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

	today = nowdate()
	allocations = frappe.get_all(
		"Leave Allocation",
		filters={
			"employee": employee,
			"docstatus": 1,
			"from_date": ["<=", today],
			"to_date": [">=", today],
		},
		fields=["leave_type", "total_leaves_allocated", "from_date", "to_date"],
	)

	out = []
	for alloc in allocations:
		try:
			balance = get_leave_balance_on(
				employee, alloc.leave_type, today, consider_all_leaves_in_the_allocation_period=True
			)
		except Exception:
			balance = 0
		total = flt(alloc.total_leaves_allocated)
		out.append(
			{
				"leave_type": alloc.leave_type,
				"balance": flt(balance, 1),
				"allocated": flt(total, 1),
				"used": flt(total - flt(balance), 1),
				"pct": round((flt(balance) / total) * 100) if total else 0,
			}
		)
	out.sort(key=lambda r: r["allocated"], reverse=True)
	return out


def _recent_requests(employee: str, limit: int = 5) -> list[dict]:
	"""One feed across leave, expense and attendance requests."""
	rows = []

	for la in frappe.get_all(
		"Leave Application",
		filters={"employee": employee},
		fields=[
			"name",
			"leave_type",
			"from_date",
			"to_date",
			"total_leave_days",
			"status",
			"leave_approver",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	):
		rows.append(
			{
				"type": "Leave",
				"name": la.name,
				"label": la.leave_type,
				"from_date": str(la.from_date) if la.from_date else None,
				"to_date": str(la.to_date) if la.to_date else None,
				"days": flt(la.total_leave_days, 1),
				"submitted": str(la.modified.date()) if la.modified else None,
				"approver": la.leave_approver,
				"status": la.status,
			}
		)

	for ec in frappe.get_all(
		"Expense Claim",
		filters={"employee": employee},
		fields=[
			"name",
			"total_claimed_amount",
			"approval_status",
			"status",
			"expense_approver",
			"posting_date",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	):
		rows.append(
			{
				"type": "Expense",
				"name": ec.name,
				"amount": flt(ec.total_claimed_amount),
				"submitted": str(ec.posting_date) if ec.posting_date else None,
				"approver": ec.expense_approver,
				"status": ec.status if ec.status not in ("Draft",) else "Draft",
			}
		)

	for ar in frappe.get_all(
		"Attendance Request",
		filters={"employee": employee},
		fields=["name", "reason", "from_date", "to_date", "docstatus", "modified"],
		order_by="modified desc",
		limit=limit,
	):
		rows.append(
			{
				"type": "Attendance",
				"name": ar.name,
				"label": ar.reason,
				"from_date": str(ar.from_date) if ar.from_date else None,
				"to_date": str(ar.to_date) if ar.to_date else None,
				"submitted": str(ar.modified.date()) if ar.modified else None,
				"approver": None,
				"status": {0: "Draft", 1: "Approved", 2: "Cancelled"}.get(ar.docstatus, "Draft"),
			}
		)

	rows.sort(key=lambda r: r.get("submitted") or "", reverse=True)
	return _attach_approver_names(rows)[:limit]


def _attach_approver_names(rows: list[dict]) -> list[dict]:
	users = {r["approver"] for r in rows if r.get("approver")}
	names = {}
	if users:
		for u in frappe.get_all("User", filters={"name": ["in", list(users)]}, fields=["name", "full_name"]):
			names[u.name] = u.full_name
	for r in rows:
		r["approver_name"] = names.get(r.get("approver")) or r.get("approver")
	return rows


def _pending_approvals(employee: str) -> list[dict]:
	"""Requests from direct reports awaiting this person. Empty for non-approvers."""
	reports = frappe.get_all("Employee", filters={"reports_to": employee, "status": "Active"}, pluck="name")
	if not reports:
		return []

	out = []
	for la in frappe.get_all(
		"Leave Application",
		filters={"employee": ["in", reports], "status": "Open", "docstatus": 0},
		fields=["name", "employee", "employee_name", "leave_type", "from_date"],
		limit=5,
	):
		out.append(
			{
				"type": "Leave",
				"name": la.name,
				"employee_name": la.employee_name,
				"detail": f"{la.leave_type}, {la.from_date}",
			}
		)

	for ec in frappe.get_all(
		"Expense Claim",
		filters={"employee": ["in", reports], "approval_status": "Draft", "docstatus": 0},
		fields=["name", "employee_name", "total_claimed_amount"],
		limit=5,
	):
		out.append(
			{
				"type": "Expense",
				"name": ec.name,
				"employee_name": ec.employee_name,
				"detail": frappe.utils.fmt_money(ec.total_claimed_amount),
			}
		)

	return out[:6]


def _out_today(company: str, employee: str) -> dict:
	today = nowdate()
	rows = frappe.get_all(
		"Leave Application",
		filters={
			"status": "Approved",
			"docstatus": 1,
			"from_date": ["<=", today],
			"to_date": [">=", today],
		},
		fields=["employee", "employee_name", "leave_type"],
		limit=20,
	)
	total = frappe.db.count("Employee", {"status": "Active", "company": company})
	people = [
		{"employee": r.employee, "employee_name": r.employee_name, "reason": r.leave_type} for r in rows
	]
	return {"people": people[:5], "count": len(people), "total": total}


def _coming_up(emp) -> list[dict]:
	"""Holidays, work anniversaries and birthdays in the next 60 days, merged."""
	today = getdate(nowdate())
	horizon = add_days(today, 60)
	items = []

	holiday_list = emp.holiday_list or frappe.db.get_value("Company", emp.company, "default_holiday_list")
	if holiday_list:
		for h in frappe.get_all(
			"Holiday",
			filters={
				"parent": holiday_list,
				"holiday_date": ["between", [today, horizon]],
				"weekly_off": 0,
			},
			fields=["holiday_date", "description"],
			order_by="holiday_date asc",
			limit=4,
		):
			items.append({"date": str(h.holiday_date), "label": h.description, "kind": "holiday"})

	for e in frappe.get_all(
		"Employee",
		filters={"status": "Active", "company": emp.company, "date_of_joining": ["is", "set"]},
		fields=["employee_name", "date_of_joining"],
		limit=200,
	):
		joined = getdate(e.date_of_joining)
		try:
			anniversary = joined.replace(year=today.year)
		except ValueError:
			continue
		if today <= anniversary <= horizon and anniversary != joined:
			years = today.year - joined.year
			items.append(
				{
					"date": str(anniversary),
					"label": f"{e.employee_name}'s work anniversary, {years} year{'s' if years != 1 else ''}",
					"kind": "anniversary",
				}
			)

	items.sort(key=lambda i: i["date"])
	return items[:5]


@frappe.whitelist()
def get_attendance(month: str | None = None) -> dict:
	"""month is any date inside the target month, defaults to today."""
	employee = get_current_employee()
	emp = _employee_doc(employee)
	anchor = getdate(month) if month else getdate(nowdate())
	start, end = get_first_day(anchor), get_last_day(anchor)

	rows = frappe.get_all(
		"Attendance",
		filters={
			"employee": employee,
			"docstatus": 1,
			"attendance_date": ["between", [start, end]],
		},
		fields=["attendance_date", "status", "working_hours", "leave_type", "in_time", "out_time"],
	)
	by_date = {str(r.attendance_date): r for r in rows}

	holiday_list = emp.holiday_list or frappe.db.get_value("Company", emp.company, "default_holiday_list")
	holidays = {}
	if holiday_list:
		for h in frappe.get_all(
			"Holiday",
			filters={"parent": holiday_list, "holiday_date": ["between", [start, end]]},
			fields=["holiday_date", "description", "weekly_off"],
		):
			holidays[str(h.holiday_date)] = h

	days = []
	cursor = start
	while cursor <= end:
		key = str(cursor)
		att = by_date.get(key)
		holiday = holidays.get(key)
		days.append(
			{
				"date": key,
				"day": getdate(cursor).day,
				"weekday": getdate(cursor).weekday(),
				"status": att.status if att else ("Holiday" if holiday else None),
				"hours": flt(att.working_hours, 1) if att and att.working_hours else None,
				"leave_type": att.leave_type if att else None,
				"holiday": holiday.description if holiday else None,
				"weekly_off": bool(holiday and holiday.weekly_off),
				"is_today": getdate(cursor) == getdate(nowdate()),
			}
		)
		cursor = add_days(cursor, 1)

	present = sum(1 for d in days if d["status"] in ("Present", "Work From Home"))
	half = sum(1 for d in days if d["status"] == "Half Day")
	on_leave = sum(1 for d in days if d["status"] == "On Leave")
	absent = sum(1 for d in days if d["status"] == "Absent")
	worked = [d["hours"] for d in days if d["hours"]]

	# days that have passed, are not holidays, and have no attendance record
	unmarked = [
		d for d in days if not d["status"] and not d["weekly_off"] and getdate(d["date"]) < getdate(nowdate())
	]

	last_log = frappe.db.get_value(
		"Employee Checkin",
		{"employee": employee},
		["time", "log_type", "device_id"],
		order_by="time desc",
		as_dict=True,
	)

	shift = None
	if emp.default_shift:
		shift = frappe.db.get_value(
			"Shift Type",
			emp.default_shift,
			["name", "start_time", "end_time"],
			as_dict=True,
		)

	requests = frappe.get_all(
		"Attendance Request",
		filters={"employee": employee},
		fields=["name", "from_date", "to_date", "reason", "docstatus"],
		order_by="from_date desc",
		limit=5,
	)

	return {
		"month": str(start),
		"month_label": anchor.strftime("%B %Y"),
		"prev_month": str(add_months(start, -1)),
		"next_month": str(add_months(start, 1)) if add_months(start, 1) <= getdate(nowdate()) else None,
		"days": days,
		"stats": {
			"present": present + half,
			"half_day": half,
			"on_leave": on_leave,
			"absent": absent,
			"unmarked": len(unmarked),
			"avg_hours": flt(sum(worked) / len(worked), 1) if worked else 0,
			"working_days": sum(1 for d in days if not d["weekly_off"] and not d["holiday"]),
		},
		"today": {
			"checked_in": bool(last_log and last_log.log_type == "IN"),
			"since": str(last_log.time) if last_log else None,
			"device": last_log.device_id if last_log else None,
		},
		"unmarked": unmarked[:5],
		"requests": [
			{
				**r,
				"status": {0: "Draft", 1: "Approved", 2: "Cancelled"}.get(r.docstatus, "Draft"),
			}
			for r in requests
		],
		"shift": shift,
		"weekly_off": _weekly_off_labels(holiday_list),
	}


def _weekly_off_labels(holiday_list: str) -> str:
	if not holiday_list:
		return ""
	rows = frappe.get_all(
		"Holiday",
		filters={"parent": holiday_list, "weekly_off": 1},
		fields=["holiday_date"],
		limit=60,
	)
	names = sorted({getdate(r.holiday_date).strftime("%A") for r in rows})
	return ", ".join(names)


@frappe.whitelist()
def get_leave() -> dict:
	employee = get_current_employee()
	emp = _employee_doc(employee)
	today = nowdate()

	applications = frappe.get_all(
		"Leave Application",
		filters={"employee": employee},
		fields=[
			"name",
			"leave_type",
			"from_date",
			"to_date",
			"total_leave_days",
			"status",
			"leave_approver",
			"description",
			"docstatus",
		],
		order_by="from_date desc",
		limit=25,
	)
	for a in applications:
		# a submitted, approved application in the past has been taken, not merely approved
		if a.docstatus == 0:
			a["display_status"] = "Draft"
		elif a.status == "Approved" and a.docstatus == 1 and getdate(a.to_date) < getdate(today):
			a["display_status"] = "Taken"
		else:
			a["display_status"] = a.status
	approvers = {a.leave_approver for a in applications if a.leave_approver}
	approver_names = {}
	if approvers:
		for u in frappe.get_all(
			"User", filters={"name": ["in", list(approvers)]}, fields=["name", "full_name"]
		):
			approver_names[u.name] = u.full_name
	for a in applications:
		a["approver_name"] = approver_names.get(a.leave_approver) or a.leave_approver

	# Team out over the next 7 days, meaning the peers under your own manager.
	# Without a manager there is no peer group, and an unfiltered reports_to would
	# match every employee who also has none.
	reports = (
		frappe.get_all(
			"Employee",
			filters={"reports_to": emp.reports_to, "status": "Active", "name": ["!=", employee]},
			pluck="name",
		)
		if emp.reports_to
		else []
	)
	team = (
		frappe.get_all(
			"Leave Application",
			filters={
				"employee": ["in", reports],
				"status": "Approved",
				"docstatus": 1,
				"to_date": [">=", today],
				"from_date": ["<=", add_days(today, 7)],
			},
			fields=["employee", "employee_name", "from_date", "to_date", "leave_type"],
			order_by="from_date asc",
			limit=8,
		)
		if reports
		else []
	)

	return {
		"balances": _leave_balances(employee),
		"applications": applications,
		"team": team,
		"allocation_period": _allocation_period(employee),
	}


def _allocation_period(employee: str) -> str:
	row = frappe.db.get_value(
		"Leave Allocation",
		{"employee": employee, "docstatus": 1, "to_date": [">=", nowdate()]},
		["from_date", "to_date"],
		as_dict=True,
	)
	if not row:
		return ""
	return f"{getdate(row.from_date).strftime('%b %Y')} to {getdate(row.to_date).strftime('%b %Y')}"


@frappe.whitelist()
def get_expenses() -> dict:
	employee = get_current_employee()

	claims = frappe.get_all(
		"Expense Claim",
		filters={"employee": employee},
		fields=[
			"name",
			"posting_date",
			"total_claimed_amount",
			"total_sanctioned_amount",
			"total_amount_reimbursed",
			"approval_status",
			"status",
			"docstatus",
			"remark",
			"currency",
			"expense_approver",
		],
		order_by="posting_date desc, modified desc",
		limit=25,
	)

	# purpose comes from the first child row, which is what people recognise
	for c in claims:
		child = frappe.db.get_value(
			"Expense Claim Detail",
			{"parent": c.name},
			["expense_type", "description"],
			as_dict=True,
		)
		c["purpose"] = (child.description or child.expense_type) if child else (c.remark or "")
		c["display_status"] = "Draft" if c.docstatus == 0 else c.status

	claimed = sum(flt(c.total_claimed_amount) for c in claims if c.docstatus == 1)
	reimbursed = sum(flt(c.total_amount_reimbursed) for c in claims)
	# A submitted claim can never be "Draft": Expense Claim.on_submit throws unless
	# approval_status is Approved or Rejected. What is actually waiting on the
	# approver is the employee's draft, which the approver reviews and submits.
	awaiting = [c for c in claims if c.docstatus == 0]

	# age of the oldest unapproved claim: the number people escalate on
	oldest_age = None
	if awaiting:
		dates = [getdate(c.posting_date) for c in awaiting if c.posting_date]
		if dates:
			oldest_age = (getdate(nowdate()) - min(dates)).days

	# The age is what people escalate on, so name who is holding the claim too.
	awaiting_rows = _attach_approver_names(
		[
			{
				"name": c.name,
				"purpose": c.purpose,
				"amount": flt(c.total_claimed_amount),
				"currency": c.currency,
				"approver": c.expense_approver,
				"days": (getdate(nowdate()) - getdate(c.posting_date)).days if c.posting_date else None,
			}
			for c in awaiting
		]
	)

	# Advances drawn but not yet settled against a claim: money the employee is
	# holding. Same formula as get_advances so the two pages cannot disagree.
	open_advances = []
	for a in frappe.get_all(
		"Employee Advance",
		filters={"employee": employee, "docstatus": 1},
		fields=["name", "purpose", "posting_date", "paid_amount", "claimed_amount", "return_amount"],
		order_by="posting_date asc",
	):
		left = flt(a.paid_amount) - flt(a.claimed_amount) - flt(a.return_amount)
		if left > 0:
			a["outstanding"] = left
			open_advances.append(a)

	return {
		"claims": claims,
		"awaiting_claims": awaiting_rows,
		"advances": {
			"rows": open_advances,
			"outstanding": sum(a["outstanding"] for a in open_advances),
		},
		"stats": {
			"claimed": claimed,
			"awaiting": sum(flt(c.total_claimed_amount) for c in awaiting),
			"awaiting_count": len(awaiting),
			"oldest_age": oldest_age,
			"reimbursed": reimbursed,
			"count": len([c for c in claims if c.docstatus == 1]),
		},
		# currency a new claim will be raised in
		"claim_currency": _claim_currency(employee),
	}


def _claim_currency(employee: str) -> str:
	emp = frappe.db.get_value("Employee", employee, ["company", "salary_currency"], as_dict=True)
	return emp.salary_currency or frappe.db.get_value("Company", emp.company, "default_currency")


@frappe.whitelist()
def get_payslips(period: str | None = None, from_date: str | None = None, to_date: str | None = None) -> dict:
	"""`period` is one of PAYSLIP_PERIODS; "custom" reads from_date/to_date instead."""
	employee = get_current_employee()

	start, end = _payslip_range(period, from_date, to_date)
	filters = {"employee": employee, "docstatus": ["!=", 2]}
	if start and end:
		filters["start_date"] = ["between", [start, end]]
	elif start:
		filters["start_date"] = [">=", start]
	elif end:
		filters["start_date"] = ["<=", end]

	slips = frappe.get_all(
		"Salary Slip",
		filters=filters,
		fields=[
			"name",
			"start_date",
			"end_date",
			"gross_pay",
			"total_deduction",
			"net_pay",
			"status",
			"docstatus",
		],
		order_by="start_date desc",
		limit=24,
	)
	for s in slips:
		s["period"] = getdate(s.start_date).strftime("%B %Y") if s.start_date else ""

	paid = [s for s in slips if s.docstatus == 1]
	ytd = {
		"gross": sum(flt(s.gross_pay) for s in paid),
		"deductions": sum(flt(s.total_deduction) for s in paid),
		"net": sum(flt(s.net_pay) for s in paid),
		"months": len(paid),
		"last_paid": str(paid[0].end_date) if paid else None,
	}

	structure = frappe.db.get_value(
		"Salary Structure Assignment",
		{"employee": employee, "docstatus": 1},
		["salary_structure", "from_date", "base"],
		order_by="from_date desc",
		as_dict=True,
	)

	return {
		"slips": slips,
		"ytd": ytd,
		"structure": structure,
		"tax": _tax_summary(employee),
		"period": period or "12m",
		"range": {"from_date": str(start) if start else None, "to_date": str(end) if end else None},
	}


# Ranges the payslip list offers, in months back from today.
PAYSLIP_PERIODS = {"3m": 3, "6m": 6, "12m": 12, "all": None}


def _payslip_range(period: str | None, from_date: str | None, to_date: str | None):
	"""Resolve a period key, or an explicit range, into (start, end) dates."""
	if period == "custom":
		return (getdate(from_date) if from_date else None, getdate(to_date) if to_date else None)

	months = PAYSLIP_PERIODS.get(period or "12m", 12)
	if months is None:
		return (None, None)

	today = getdate(nowdate())
	# from the first of the month N-1 back, so "3 months" means three whole ones
	return (get_first_day(add_months(today, -(months - 1))), get_last_day(today))


@frappe.whitelist()
def get_payslip(name: str) -> dict:
	"""One payslip, in full. A payslip is only ever read here, never edited."""
	employee = get_current_employee()
	slip = frappe.get_doc("Salary Slip", name)

	# the whole point of the portal is that you see your own documents and no others
	if slip.employee != employee:
		raise frappe.PermissionError(_("This payslip belongs to someone else."))
	if slip.docstatus == 2:
		raise frappe.DoesNotExistError(_("This payslip has been cancelled."))

	def components(rows):
		return [
			{
				"salary_component": r.salary_component,
				"amount": flt(r.amount),
				"year_to_date": flt(r.year_to_date),
			}
			for r in rows
			# statistical components are scaffolding for the formulae, not pay
			if not r.statistical_component and not r.do_not_include_in_total
		]

	return {
		"name": slip.name,
		"period": getdate(slip.start_date).strftime("%B %Y") if slip.start_date else "",
		"start_date": str(slip.start_date) if slip.start_date else None,
		"end_date": str(slip.end_date) if slip.end_date else None,
		"posting_date": str(slip.posting_date) if slip.posting_date else None,
		"status": slip.status if slip.docstatus == 1 else "Draft",
		"docstatus": slip.docstatus,
		"currency": slip.currency,
		"gross_pay": flt(slip.gross_pay),
		"total_deduction": flt(slip.total_deduction),
		"net_pay": flt(slip.net_pay),
		"rounded_total": flt(slip.rounded_total),
		"total_in_words": slip.total_in_words,
		"year_to_date": flt(slip.year_to_date),
		"gross_year_to_date": flt(slip.gross_year_to_date),
		"earnings": components(slip.earnings),
		"deductions": components(slip.deductions),
		"attendance": {
			"total_working_days": flt(slip.total_working_days),
			"payment_days": flt(slip.payment_days),
			"leave_without_pay": flt(slip.leave_without_pay),
			"absent_days": flt(slip.absent_days),
		},
		"salary_structure": slip.salary_structure,
		"mode_of_payment": slip.mode_of_payment,
	}


@frappe.whitelist()
def payslip_pdf(name: str, inline: int = 0):
	"""The payslip as a PDF, rendered with the print format desk is configured to use.

	frappe.utils.print_format.download_pdf would render the same thing, but it
	only checks the Salary Slip read permission. On a site without a User
	Permission tying employees to their own record that lets anyone with the
	Employee role fetch a colleague's slip, so ownership is checked here first.
	"""
	employee = get_current_employee()
	slip = frappe.db.get_value("Salary Slip", name, ["employee", "docstatus"], as_dict=True)

	if not slip or slip.docstatus == 2:
		raise frappe.DoesNotExistError(_("This payslip does not exist."))
	if slip.employee != employee:
		raise frappe.PermissionError(_("This payslip belongs to someone else."))

	# No print format is named on purpose: printview then falls back to the
	# doctype default and finally to Standard. no_letterhead=None likewise
	# leaves the letterhead decision to Print Settings.
	pdf = frappe.get_print("Salary Slip", name, as_pdf=True, no_letterhead=None)

	frappe.local.response.filename = "{}.pdf".format(name.replace(" ", "-").replace("/", "-"))
	frappe.local.response.filecontent = pdf
	# inline opens in the browser's PDF viewer to print from; otherwise it saves
	frappe.local.response.type = "pdf" if cint(inline) else "download"


# A guard against a runaway request: rendering PDFs is the expensive part, and
# the list itself never offers more than this many rows.
MAX_BULK_PAYSLIPS = 24


def _own_payslip(name: str, employee: str) -> dict:
	slip = frappe.db.get_value(
		"Salary Slip", name, ["name", "employee", "docstatus", "start_date"], as_dict=True
	)
	if not slip or slip.docstatus == 2:
		raise frappe.DoesNotExistError(_("This payslip does not exist."))
	if slip.employee != employee:
		raise frappe.PermissionError(_("This payslip belongs to someone else."))
	return slip


@frappe.whitelist(methods=["POST"])
def payslips_zip(names: str | list):
	"""Several payslips as one zip, each rendered with the desk print format."""
	import io
	import zipfile

	employee = get_current_employee()
	names = frappe.parse_json(names) if isinstance(names, str) else names
	if not names:
		frappe.throw(_("Select at least one payslip to download."))
	if len(names) > MAX_BULK_PAYSLIPS:
		frappe.throw(_("You can download at most {0} payslips at once.").format(MAX_BULK_PAYSLIPS))

	buffer = io.BytesIO()
	with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
		for name in names:
			slip = _own_payslip(name, employee)
			# name the entry by period, so the zip reads as months not doc ids
			label = getdate(slip.start_date).strftime("%Y-%m") if slip.start_date else slip.name
			pdf = frappe.get_print("Salary Slip", name, as_pdf=True, no_letterhead=None)
			archive.writestr(f"{label}-payslip.pdf", pdf)

	frappe.local.response.filename = "payslips.zip"
	frappe.local.response.filecontent = buffer.getvalue()
	frappe.local.response.type = "download"


def _tax_summary(employee: str) -> dict:
	declaration = frappe.db.get_value(
		"Employee Tax Exemption Declaration",
		{"employee": employee, "docstatus": 1},
		["name", "total_declared_amount", "payroll_period"],
		order_by="creation desc",
		as_dict=True,
	)
	period_end = None
	if declaration and declaration.payroll_period:
		period_end = frappe.db.get_value("Payroll Period", declaration.payroll_period, "end_date")
	return {
		"declared": flt(declaration.total_declared_amount) if declaration else 0,
		"has_declaration": bool(declaration),
		"period_end": str(period_end) if period_end else None,
	}


@frappe.whitelist()
def get_advances() -> dict:
	employee = get_current_employee()

	advances = frappe.get_all(
		"Employee Advance",
		filters={"employee": employee},
		fields=[
			"name",
			"posting_date",
			"purpose",
			"advance_amount",
			"paid_amount",
			"claimed_amount",
			"return_amount",
			"status",
			"docstatus",
		],
		order_by="posting_date desc",
		limit=20,
	)

	outstanding = sum(
		flt(a.paid_amount) - flt(a.claimed_amount) - flt(a.return_amount)
		for a in advances
		if a.docstatus == 1
	)
	repaid = sum(flt(a.claimed_amount) + flt(a.return_amount) for a in advances if a.docstatus == 1)
	total = sum(flt(a.paid_amount) for a in advances if a.docstatus == 1)

	return {
		"advances": advances,
		"stats": {
			"outstanding": outstanding,
			"repaid": repaid,
			"total": total,
			"pct_repaid": round((repaid / total) * 100) if total else 0,
		},
	}


@frappe.whitelist()
def get_directory(
	search: str | None = None, department: str | None = None, branch: str | None = None
) -> dict:
	"""Public subset only. Never returns personal, pay or document fields."""
	emp = _employee_doc()
	filters = {"status": "Active", "company": emp.company}
	if department:
		filters["department"] = department
	if branch:
		filters["branch"] = branch
	or_filters = None
	if search:
		or_filters = {
			"employee_name": ["like", f"%{search}%"],
			"designation": ["like", f"%{search}%"],
		}

	people = frappe.get_all(
		"Employee",
		filters=filters,
		or_filters=or_filters,
		fields=list(PUBLIC_FIELDS),
		order_by="employee_name asc",
		limit=200,
	)

	# availability today, which is the reason to open a directory rather than a contact list
	today = nowdate()
	on_leave = {
		r.employee: r.leave_type
		for r in frappe.get_all(
			"Leave Application",
			filters={
				"status": "Approved",
				"docstatus": 1,
				"from_date": ["<=", today],
				"to_date": [">=", today],
			},
			fields=["employee", "leave_type"],
		)
	}
	for p in people:
		p["department"] = (p.department or "").split(" - ")[0] or None
		p["availability"] = "On leave" if p.name in on_leave else "Available"
		p["is_self"] = p.name == emp.name

	departments = sorted({p["department"] for p in people if p["department"]})
	branches = sorted({p.branch for p in people if p.branch})

	return {
		"people": people,
		"departments": departments,
		"branches": branches,
		"total": len(people),
	}


@frappe.whitelist()
def get_colleague(employee: str) -> dict:
	"""Reduced surface for a colleague. Restricted sections are absent, not disabled."""
	me = _employee_doc()
	row = frappe.db.get_value("Employee", employee, list(PUBLIC_FIELDS), as_dict=True)
	if not row or frappe.db.get_value("Employee", employee, "company") != me.company:
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	today = nowdate()
	leave = frappe.db.get_value(
		"Leave Application",
		{
			"employee": employee,
			"status": "Approved",
			"docstatus": 1,
			"from_date": ["<=", today],
			"to_date": [">=", today],
		},
		["to_date"],
		as_dict=True,
	)

	manager = None
	if row.reports_to:
		manager = frappe.db.get_value(
			"Employee", row.reports_to, ["name", "employee_name", "designation", "image"], as_dict=True
		)

	reports = frappe.get_all(
		"Employee",
		filters={"reports_to": employee, "status": "Active"},
		fields=["name", "employee_name", "image", "designation"],
		limit=20,
	)

	return {
		"employee": {
			**row,
			"department": (row.department or "").split(" - ")[0] or None,
			"tenure": _tenure(row.date_of_joining),
		},
		"availability": {
			"status": "On leave" if leave else "Available",
			"until": str(leave.to_date) if leave else None,
		},
		"manager": manager,
		"reports": reports,
	}


@frappe.whitelist()
def get_org_chart() -> dict:
	emp = _employee_doc()

	def node(name):
		if not name:
			return None
		row = frappe.db.get_value(
			"Employee",
			name,
			["name", "employee_name", "designation", "image", "reports_to"],
			as_dict=True,
		)
		if not row:
			return None
		row["report_count"] = frappe.db.count("Employee", {"reports_to": name, "status": "Active"})
		return row

	me = node(emp.name)
	manager = node(emp.reports_to)
	skip = node(manager.reports_to) if manager else None

	peers = []
	if emp.reports_to:
		peers = frappe.get_all(
			"Employee",
			filters={"reports_to": emp.reports_to, "status": "Active"},
			fields=["name", "employee_name", "designation", "image"],
			order_by="employee_name asc",
			limit=24,
		)
		for p in peers:
			p["report_count"] = frappe.db.count("Employee", {"reports_to": p.name, "status": "Active"})

	my_reports = frappe.get_all(
		"Employee",
		filters={"reports_to": emp.name, "status": "Active"},
		fields=["name", "employee_name", "designation", "image"],
		order_by="employee_name asc",
		limit=24,
	)

	return {
		"me": me,
		"manager": manager,
		"skip": skip,
		"peers": peers,
		"reports": my_reports,
	}


@frappe.whitelist()
def get_holidays() -> dict:
	emp = _employee_doc()
	holiday_list = emp.holiday_list or frappe.db.get_value("Company", emp.company, "default_holiday_list")
	if not holiday_list:
		return {"holidays": [], "list_name": None, "stats": {}, "weekly_off": ""}

	rows = frappe.get_all(
		"Holiday",
		filters={"parent": holiday_list, "weekly_off": 0},
		fields=["holiday_date", "description"],
		order_by="holiday_date asc",
		limit=60,
	)
	today = getdate(nowdate())
	holidays = []
	for r in rows:
		d = getdate(r.holiday_date)
		holidays.append(
			{
				"date": str(d),
				"weekday": d.strftime("%A"),
				"description": r.description,
				"is_past": d < today,
				# a Saturday holiday is worth nothing to most people, so say so
				"falls_on_off": d.weekday() >= 5,
			}
		)

	remaining = [h for h in holidays if not h["is_past"]]
	return {
		"list_name": holiday_list,
		"holidays": holidays,
		"weekly_off": _weekly_off_labels(holiday_list),
		"branch": emp.branch,
		"stats": {
			"total": len(holidays),
			"remaining": len(remaining),
			"next": remaining[0] if remaining else None,
		},
	}


@frappe.whitelist()
def get_documents() -> dict:
	"""Company-wide shared files, plus a pointer to the employee's own documents."""
	emp = _employee_doc()

	company_docs = frappe.get_all(
		"File",
		filters={"is_private": 0, "is_folder": 0, "attached_to_doctype": ["is", "not set"]},
		fields=["name", "file_name", "file_url", "file_size", "modified"],
		order_by="modified desc",
		limit=25,
	)

	mine = frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Employee", "attached_to_name": emp.name},
		fields=["name", "file_name", "file_url", "file_size", "is_private", "modified"],
		order_by="modified desc",
		limit=25,
	)

	return {
		"company": company_docs,
		"mine": mine,
	}


@frappe.whitelist()
def get_profile() -> dict:
	"""Own profile. Every field, split by who owns it."""
	emp = _employee_doc()

	manager = None
	if emp.reports_to:
		manager = frappe.db.get_value(
			"Employee",
			emp.reports_to,
			["name", "employee_name", "designation", "image"],
			as_dict=True,
		)
	skip = None
	if manager:
		skip_id = frappe.db.get_value("Employee", manager.name, "reports_to")
		if skip_id:
			skip = frappe.db.get_value(
				"Employee", skip_id, ["name", "employee_name", "designation", "image"], as_dict=True
			)

	peers = []
	if emp.reports_to:
		peers = frappe.get_all(
			"Employee",
			filters={
				"reports_to": emp.reports_to,
				"status": "Active",
				"name": ["!=", emp.name],
			},
			fields=["name", "employee_name", "image"],
			limit=12,
		)

	history = []
	for row in frappe.get_all(
		"Employee Internal Work History",
		filters={"parent": emp.name},
		fields=["designation", "department", "from_date", "to_date"],
		order_by="from_date desc",
		limit=10,
	):
		history.append(
			{
				"date": str(row.from_date) if row.from_date else None,
				"label": f"{row.designation or ''}{', ' + row.department.split(' - ')[0] if row.department else ''}".strip(
					", "
				),
			}
		)
	if emp.date_of_joining:
		history.append({"date": str(emp.date_of_joining), "label": _("Joined the company")})

	slips = frappe.get_all(
		"Salary Slip",
		filters={"employee": emp.name, "docstatus": 1},
		fields=["name", "start_date", "gross_pay", "total_deduction", "net_pay"],
		order_by="start_date desc",
		limit=3,
	)
	for s in slips:
		s["period"] = getdate(s.start_date).strftime("%B %Y") if s.start_date else ""

	documents = frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Employee", "attached_to_name": emp.name},
		fields=["name", "file_name", "file_url", "file_size", "modified"],
		order_by="modified desc",
		limit=20,
	)

	shift = None
	if emp.default_shift:
		shift = frappe.db.get_value(
			"Shift Type", emp.default_shift, ["name", "start_time", "end_time"], as_dict=True
		)

	upcoming_leave = frappe.get_all(
		"Leave Application",
		filters={"employee": emp.name, "to_date": [">=", nowdate()]},
		fields=["leave_type", "from_date", "to_date", "total_leave_days", "status"],
		order_by="from_date asc",
		limit=4,
	)

	return {
		"employee": {
			"name": emp.name,
			"employee_name": emp.employee_name,
			"image": emp.image,
			"designation": emp.designation,
			"department": (emp.department or "").split(" - ")[0] or None,
			"branch": emp.branch,
			"status": emp.status,
			"employment_type": emp.employment_type,
			"grade": emp.grade,
			"employee_number": emp.employee_number or emp.name,
			"date_of_joining": str(emp.date_of_joining) if emp.date_of_joining else None,
			"tenure": _tenure(emp.date_of_joining),
			"company_email": emp.company_email,
			"shift": shift,
		},
		"personal": {
			"employee_name": emp.employee_name,
			"date_of_birth": str(emp.date_of_birth) if emp.date_of_birth else None,
			"gender": emp.gender,
			"blood_group": emp.blood_group,
			"marital_status": emp.marital_status,
		},
		"contact": {
			"company_email": emp.company_email,
			"personal_email": emp.personal_email,
			"cell_number": emp.cell_number,
		},
		"addresses": {
			"current_address": emp.current_address,
			"permanent_address": emp.permanent_address,
		},
		"emergency": {
			"person_to_be_contacted": emp.person_to_be_contacted,
			"relation": emp.relation,
			"emergency_phone_number": emp.emergency_phone_number,
		},
		"position": {
			"designation": emp.designation,
			"department": (emp.department or "").split(" - ")[0] or None,
			"employment_type": emp.employment_type,
			"grade": emp.grade,
			"branch": emp.branch,
		},
		"reporting": {"manager": manager, "skip": skip, "peers": peers},
		"history": history,
		"pay": {
			"slips": slips,
			"bank": {
				"bank_name": emp.bank_name,
				"account": _mask(emp.bank_ac_no),
				"ifsc": emp.ifsc_code,
			},
			"tax": _tax_summary(emp.name),
		},
		"time": {
			"balances": _leave_balances(emp.name),
			"shift": shift,
			"holiday_list": emp.holiday_list,
			"weekly_off": _weekly_off_labels(emp.holiday_list),
			"upcoming_leave": upcoming_leave,
		},
		"documents": documents,
		"field_ownership": {"employee": list(EMPLOYEE_OWNED), "hr": list(HR_OWNED)},
	}


@frappe.whitelist()
def update_profile(values: str | dict) -> dict:
	"""Save employee-owned fields only. Anything else is silently refused."""
	if isinstance(values, str):
		values = frappe.parse_json(values)

	rejected = [k for k in values if k not in EMPLOYEE_OWNED]
	if rejected:
		frappe.throw(
			_("These fields are managed by HR and cannot be changed here: {0}").format(", ".join(rejected)),
			frappe.PermissionError,
		)

	employee = get_current_employee()
	doc = frappe.get_doc("Employee", employee)
	for field, value in values.items():
		doc.set(field, value)
	doc.flags.ignore_permissions = True
	doc.save()
	frappe.db.commit()  # nosemgrep

	return {"ok": True}


MAX_ATTACHMENTS = 5
MAX_ATTACHMENT_MB = 10


def _validated_attachments(attachments: str | list | None) -> list[dict]:
	"""Decode and screen portal uploads before anything touches the database."""
	import base64
	from mimetypes import guess_type

	from frappe.handler import ALLOWED_MIMETYPES

	if isinstance(attachments, str):
		attachments = frappe.parse_json(attachments)
	if not attachments:
		return []
	if not isinstance(attachments, list) or len(attachments) > MAX_ATTACHMENTS:
		frappe.throw(_("You can attach at most {0} files").format(MAX_ATTACHMENTS))

	files = []
	for a in attachments:
		filename = (a.get("filename") or "").strip()
		if not filename or guess_type(filename)[0] not in ALLOWED_MIMETYPES:
			frappe.throw(_("{0}: only images, PDFs and office documents can be attached").format(filename))

		try:
			content = base64.b64decode(a.get("content") or "", validate=True)
		except Exception:
			frappe.throw(_("Could not read the attached file {0}").format(filename))

		if not content or len(content) > MAX_ATTACHMENT_MB * 1024 * 1024:
			frappe.throw(_("Attachments must be non-empty and under {0} MB").format(MAX_ATTACHMENT_MB))

		files.append({"file_name": filename, "content": content})

	return files


def _exchange_rate(from_currency: str, to_currency: str, on_date) -> float:
	if not from_currency or from_currency == to_currency:
		return 1

	from erpnext.setup.utils import get_exchange_rate

	return flt(get_exchange_rate(from_currency, to_currency, str(on_date))) or 1


@frappe.whitelist(methods=["POST"])
def mark_checkin(log_type: str = "IN") -> dict:
	if log_type not in ("IN", "OUT"):
		frappe.throw(_("Invalid log type"))

	employee = get_current_employee()
	last = frappe.db.get_value("Employee Checkin", {"employee": employee}, "log_type", order_by="time desc")
	if last == log_type:
		frappe.throw(_("You are already checked {0}.").format("in" if log_type == "IN" else "out"))

	doc = frappe.new_doc("Employee Checkin")
	doc.employee = employee
	doc.log_type = log_type
	doc.time = frappe.utils.now_datetime()
	doc.insert(ignore_permissions=True)
	frappe.db.commit()  # nosemgrep

	return {"ok": True, "log_type": log_type, "time": str(doc.time)}


@frappe.whitelist()
def get_profile_field_options() -> dict:
	"""Select options for the edit dialog, read from the doctype rather than hardcoded."""
	meta = frappe.get_meta("Employee")
	out = {}
	for fieldname in ("gender", "blood_group", "marital_status"):
		df = meta.get_field(fieldname)
		if not df:
			continue
		if df.fieldtype == "Select":
			out[fieldname] = [o for o in (df.options or "").split("\n") if o]
		elif df.fieldtype == "Link":
			out[fieldname] = frappe.get_all(df.options, pluck="name", limit=50)
	return out
