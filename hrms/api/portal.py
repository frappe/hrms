"""API for the Employee Portal (studio/employee_portal).

Reads go through frappe.get_list, so permissions apply. frappe.get_all is used only for the
session user's own records, or where HR Settings shares the data (see the docstrings).
"""

import frappe
from frappe import _
from frappe.utils import add_days, cint, date_diff, get_first_day, getdate, now_datetime

from hrms.controllers.employee_reminders import get_employees_having_an_event_today
from hrms.hr.doctype.leave_application.leave_application import get_leave_details
from hrms.hr.doctype.shift_assignment.shift_assignment import get_employee_shift
from hrms.utils.holiday_list import get_holiday_list_for_employee

EMPLOYEE_FIELDS = [
	"name",
	"employee_name",
	"first_name",
	"image",
	"company",
	"department",
	"date_of_joining",
	"final_confirmation_date",
	"resignation_letter_date",
	"relieving_date",
]
UPCOMING_LIMIT = 5
EVENTS_LIMIT = 8
EVENT_REMINDER_SETTINGS = {
	"birthday": "send_birthday_reminders",
	"work_anniversary": "send_work_anniversary_reminders",
}
DEFAULT_ONBOARDING_DAYS = 30


@frappe.whitelist()
def get_context() -> dict:
	employee = get_session_employee()
	return {
		"user": frappe.db.get_value(
			"User", frappe.session.user, ["full_name", "first_name", "user_image as image"], as_dict=True
		),
		"employee": {
			"employee_name": employee.employee_name,
			"first_name": employee.first_name,
			"image": employee.image,
			"company": employee.company,
		}
		if employee
		else None,
		"nav": get_nav(employee),
		"checkin_enabled": is_checkin_enabled(),
		# Employee Checkin needs coordinates while geolocation tracking is on
		"checkin_needs_location": bool(
			frappe.db.get_single_value("HR Settings", "allow_geolocation_tracking")
		),
	}


@frappe.whitelist()
def get_home() -> dict:
	employee = get_session_employee()
	if not employee:
		return {}

	onboarding = get_onboarding(employee.name)
	return {
		"shift": get_shift_status(employee),
		"leave_balance": get_leave_balance(employee),
		"absent_count": get_absent_count(employee),
		"first_month": get_first_month(employee, onboarding) if onboarding else None,
		"todos": get_todos(employee, onboarding),
		"upcoming": get_upcoming(employee),
		"out_today": get_out_today(employee),
		"events": get_company_events(employee),
		"company": employee.company,
	}


@frappe.whitelist(methods=["POST"])
def check_in(log_type: str, latitude: float | None = None, longitude: float | None = None) -> dict:
	if not is_checkin_enabled():
		frappe.throw(_("Check-in from the portal is disabled in HR Settings"), frappe.PermissionError)
	if log_type not in ("IN", "OUT"):
		frappe.throw(_("Log type must be IN or OUT"))

	employee = get_session_employee()
	if not employee:
		frappe.throw(_("No active employee is linked to your user"), frappe.PermissionError)

	checkin = frappe.get_doc(
		{
			"doctype": "Employee Checkin",
			"employee": employee.name,
			"log_type": log_type,
			"time": now_datetime(),
			"latitude": latitude,
			"longitude": longitude,
		}
	).insert()
	return {"log_type": checkin.log_type, "time": checkin.time}


def get_session_employee() -> frappe._dict | None:
	return frappe.db.get_value(
		"Employee", {"user_id": frappe.session.user, "status": "Active"}, EMPLOYEE_FIELDS, as_dict=True
	)


def get_nav(employee: frappe._dict | None) -> dict:
	if not employee:
		return {"manages": False, "is_hr": False, "todo_count": 0, "onboarding": None, "resigned": False}

	onboarding = get_onboarding(employee.name)
	return {
		"manages": bool(frappe.db.exists("Employee", {"reports_to": employee.name, "status": "Active"})),
		"is_hr": bool({"HR User", "HR Manager"} & set(frappe.get_roles())),
		"todo_count": len(get_todos(employee, onboarding)),
		"onboarding": onboarding,
		"resigned": bool(employee.resignation_letter_date or employee.relieving_date),
	}


def get_onboarding(employee: str) -> str | None:
	# employees can't read Employee Onboarding, so read their own in-progress one directly
	return frappe.db.get_value(
		"Employee Onboarding",
		{"employee": employee, "boarding_status": ["in", ["Pending", "In Process"]], "docstatus": ["<", 2]},
		"name",
	)


def is_checkin_enabled() -> bool:
	return bool(frappe.db.get_single_value("HR Settings", "allow_employee_checkin_from_mobile_app"))


def get_shift_status(employee: frappe._dict) -> dict:
	shift = get_employee_shift(employee.name, now_datetime(), consider_default_shift=True)
	last_log_type = frappe.db.get_value(
		"Employee Checkin",
		{"employee": employee.name, "time": [">=", getdate()]},
		"log_type",
		order_by="time desc",
	)
	return {
		"shift_type": shift.get("shift_type").name if shift.get("shift_type") else None,
		"last_log_type": last_log_type,
	}


def get_leave_balance(employee: frappe._dict) -> float:
	allocation = get_leave_details(employee.name, getdate())["leave_allocation"]
	return sum(details.get("remaining_leaves") or 0 for details in allocation.values())


def get_absent_count(employee: frappe._dict) -> int:
	return frappe.db.count(
		"Attendance",
		{
			"employee": employee.name,
			"status": "Absent",
			"docstatus": 1,
			"attendance_date": ["between", [get_first_day(getdate()), getdate()]],
		},
	)


def get_first_month(employee: frappe._dict, onboarding: str) -> dict:
	begins_on = frappe.db.get_value("Employee Onboarding", onboarding, "boarding_begins_on")
	activities = frappe.get_all(
		"Employee Boarding Activity",
		filters={"parent": onboarding, "parenttype": "Employee Onboarding"},
		fields=["begin_on", "duration"],
	)
	start = begins_on or employee.date_of_joining or getdate()
	plan_days = max(((row.begin_on or 0) + row.duration for row in activities if row.duration), default=0)
	return {"day": date_diff(getdate(), start) + 1, "of": plan_days or DEFAULT_ONBOARDING_DAYS}


def get_todos(employee: frappe._dict, onboarding: str | None) -> list[dict]:
	return [
		*get_approval_todos(),
		*get_self_appraisal_todos(employee),
		*(get_onboarding_todos() if onboarding else []),
	]


def get_approval_todos() -> list[dict]:
	"""Leave applications and expense claims waiting on the session user as approver."""
	user = frappe.session.user
	leaves = frappe.get_list(
		"Leave Application",
		filters={"leave_approver": user, "status": "Open", "docstatus": 0},
		fields=["name", "employee", "employee_name", "leave_type", "from_date", "creation"],
	)
	claims = frappe.get_list(
		"Expense Claim",
		filters={"expense_approver": user, "approval_status": "Draft", "docstatus": 0},
		fields=["name", "employee", "employee_name", "creation"],
	)
	images = get_employee_images([row.employee for row in leaves + claims])
	return [
		{
			"id": f"leave:{leave.name}",
			"kind": "leave_approval",
			"title": leave.leave_type,
			"person": {"name": leave.employee_name, "image": images.get(leave.employee)},
			"starts": leave.from_date,
			"sent": leave.creation,
		}
		for leave in leaves
	] + [
		{
			"id": f"claim:{claim.name}",
			"kind": "expense_approval",
			"title": _("Expense claim"),
			"person": {"name": claim.employee_name, "image": images.get(claim.employee)},
			"sent": claim.creation,
		}
		for claim in claims
	]


def get_self_appraisal_todos(employee: frappe._dict) -> list[dict]:
	appraisals = frappe.get_list(
		"Appraisal",
		filters={"employee": employee.name, "docstatus": 0, "self_score": 0},
		fields=["name", "appraisal_cycle"],
	)
	todos = []
	for appraisal in appraisals:
		cycle = frappe.db.get_value(
			"Appraisal Cycle", appraisal.appraisal_cycle, ["cycle_name", "status", "end_date"], as_dict=True
		)
		if cycle and cycle.status == "In Progress":
			todos.append(
				{
					"id": f"appraisal:{appraisal.name}",
					"kind": "self_appraisal",
					"title": _("Write your self-appraisal"),
					"subtitle": _("{0} review").format(cycle.cycle_name),
					"icon": "lucide-target",
					"due": cycle.end_date,
				}
			)
	return todos


def get_onboarding_todos() -> list[dict]:
	"""Open onboarding tasks assigned to the session user."""
	activities = frappe.get_all(
		"Employee Boarding Activity",
		filters={"parenttype": "Employee Onboarding", "user": frappe.session.user, "task": ["is", "set"]},
		fields=["activity_name", "task"],
	)
	todos = []
	for activity in activities:
		task = frappe.db.get_value("Task", activity.task, ["status", "exp_end_date"], as_dict=True)
		if task and task.status not in ("Completed", "Cancelled"):
			todos.append(
				{
					"id": f"task:{activity.task}",
					"kind": "onboarding",
					"title": activity.activity_name,
					"subtitle": _("Your first month"),
					"icon": "lucide-list-checks",
					"due": task.exp_end_date,
				}
			)
	return todos


def get_employee_images(employees: list[str]) -> dict[str, str | None]:
	if not employees:
		return {}
	rows = frappe.get_list(
		"Employee", filters={"name": ["in", list(set(employees))]}, fields=["name", "image"]
	)
	return {row.name: row.image for row in rows}


def get_upcoming(employee: frappe._dict) -> list[dict]:
	rows = [*get_upcoming_leaves(employee), *get_upcoming_holidays(employee)]
	if employee.final_confirmation_date and getdate(employee.final_confirmation_date) >= getdate():
		rows.append(
			{
				"kind": "probation",
				"title": _("Probation ends"),
				"date": employee.final_confirmation_date,
				"months": get_months_between(employee.date_of_joining, employee.final_confirmation_date),
			}
		)
	return sorted(rows, key=lambda row: row["date"])[:UPCOMING_LIMIT]


def get_upcoming_leaves(employee: frappe._dict) -> list[dict]:
	"""Approved and open leave applications from today."""
	leaves = frappe.get_list(
		"Leave Application",
		filters={
			"employee": employee.name,
			"status": ["in", ["Approved", "Open"]],
			"docstatus": ["<", 2],
			"from_date": [">=", getdate()],
		},
		fields=["leave_type", "from_date", "total_leave_days", "status"],
		order_by="from_date asc",
		limit=UPCOMING_LIMIT,
	)
	return [
		{
			"kind": "leave",
			"title": leave.leave_type,
			"date": leave.from_date,
			"days": leave.total_leave_days,
			"approved": leave.status == "Approved",
		}
		for leave in leaves
	]


def get_upcoming_holidays(employee: frappe._dict) -> list[dict]:
	holiday_list = get_holiday_list_for_employee(employee.name, raise_exception=False)
	if not holiday_list:
		return []

	holidays = frappe.get_all(
		"Holiday",
		filters={"parent": holiday_list, "holiday_date": [">=", getdate()], "weekly_off": 0},
		fields=["description", "holiday_date"],
		order_by="holiday_date asc",
		limit=UPCOMING_LIMIT,
	)
	return [
		{
			"kind": "holiday",
			"title": frappe.utils.strip_html(holiday.description),
			"date": holiday.holiday_date,
		}
		for holiday in holidays
	]


def get_months_between(start, end) -> int:
	start, end = getdate(start), getdate(end)
	return (end.year - start.year) * 12 + end.month - start.month


def get_out_today(employee: frappe._dict) -> list[dict]:
	"""Approved leave today. Like the leave calendar, the whole department is shown only when
	HR Settings allows it; otherwise only leave the user has permission to read."""
	today = getdate()
	filters = {
		"employee": ["!=", employee.name],
		"status": "Approved",
		"docstatus": 1,
		"from_date": ["<=", today],
		"to_date": [">=", today],
	}
	fields = ["employee", "employee_name", "to_date"]

	if employee.department and cint(
		frappe.db.get_single_value("HR Settings", "show_leaves_of_all_department_members_in_calendar")
	):
		filters.update({"department": employee.department, "company": employee.company})
		leaves = frappe.get_all("Leave Application", filters=filters, fields=fields)
	else:
		leaves = frappe.get_list("Leave Application", filters=filters, fields=fields)

	images = get_employee_images([leave.employee for leave in leaves])
	return [
		{
			"employee_name": leave.employee_name,
			"image": images.get(leave.employee),
			"back_on": add_days(leave.to_date, 1),
		}
		for leave in leaves
	]


def get_company_events(employee: frappe._dict) -> list[dict]:
	"""Birthdays and work anniversaries today, only when HR Settings sends reminders for them.
	Shares what those reminder emails already share: name and image."""
	events = []
	for event_type, setting in EVENT_REMINDER_SETTINGS.items():
		if not cint(frappe.db.get_single_value("HR Settings", setting)):
			continue

		for person in get_employees_having_an_event_today(event_type).get(employee.company, []):
			if person.user_id == frappe.session.user:
				continue
			event = {"employee_name": person.name, "image": person.image, "kind": event_type}
			if event_type == "work_anniversary":
				event["years"] = getdate().year - getdate(person.date_of_joining).year
			events.append(event)

	return events[:EVENTS_LIMIT]
