"""The chart is the company directory: it shows every active employee of a company the user may
see, not only the records they may read. `check_access` gates each endpoint, and reads select
directory fields only. HR Settings can limit the chart to HR.
"""

from datetime import date

import frappe
from frappe import _
from frappe.utils import add_days, cint, escape_html, getdate

from hrms.utils.holiday_list import get_holiday_list_ranges_for_employees, get_holidays_in_ranges_map

PAGE = "organizational-chart"
TEAM_PREVIEW_SIZE = 3
SEARCH_LIMIT = 20
SEARCH_TEXT_LIMIT = 140
# Expand all is refused above this many employees
EXPAND_ALL_LIMIT = 1000
# how far ahead to look for an employee's return from leave
RETURN_LOOKAHEAD_DAYS = 60
# how long someone shows as a new joiner in the directory
NEW_JOINER_DAYS = 30

# Directory fields only. No user_id or preferred email, which can be personal addresses.
NODE_FIELDS = [
	"name",
	"employee_name",
	"image",
	"reports_to",
	"designation",
	"department.department_name as department",
	"branch",
	"company_email",
]


def check_access(company: str) -> set[str]:
	"""Throw unless the user may see the chart of `company`. Returns every company they may see."""
	# a page without roles is open to everyone, portal users included
	if frappe.get_cached_value("User", frappe.session.user, "user_type") != "System User":
		frappe.throw(_("You do not have access to the Organizational Chart"), frappe.PermissionError)

	if not frappe.get_cached_doc("Page", PAGE).is_permitted():
		frappe.throw(_("You do not have access to the Organizational Chart"), frappe.PermissionError)

	companies = set(get_allowed_companies())
	if company not in companies:
		frappe.throw(
			_("You do not have access to the Organizational Chart of {0}").format(
				frappe.bold(escape_html(company))
			),
			frappe.PermissionError,
		)
	return companies


def get_allowed_companies() -> list[str]:
	"""HR sees every company they have access to. An employee sees only their own, and only if HR
	Settings allows it: reading the Company list is a far wider permission than working there."""
	companies = frappe.get_list("Company", pluck="name", order_by="name")
	if can_read_all_employees():
		return companies
	if not is_shown_to_all_employees():
		return []

	own_company = frappe.db.get_value(
		"Employee", {"user_id": frappe.session.user, "status": "Active"}, "company"
	)
	return [company for company in companies if company == own_company]


def can_read_all_employees() -> bool:
	return frappe.has_permission("Employee", ptype="read") and not frappe.permissions.get_user_permissions(
		frappe.session.user
	).get("Employee")


def is_shown_to_all_employees() -> bool:
	return bool(frappe.db.get_single_value("HR Settings", "show_org_chart_to_all_employees"))


@frappe.whitelist()
def get_chart_context() -> dict:
	"""Companies to pick from, the one to open, and the user's own employee"""
	companies = get_allowed_companies()
	employee = frappe.db.get_value(
		"Employee", {"user_id": frappe.session.user, "status": "Active"}, ["name", "company"], as_dict=True
	)

	company = (employee and employee.company) or frappe.defaults.get_user_default("Company")
	if company not in companies:
		company = companies[0] if companies else None

	return {
		"companies": companies,
		"company": company,
		"employee": employee and employee.name,
		# so the page can say why it is empty
		"hidden_from_employees": not companies and not is_shown_to_all_employees(),
	}


@frappe.whitelist()
def get_children(company: str, parent: str | None = None) -> list[dict]:
	"""Direct reports of `parent`, or the top of the chart when no parent is given"""
	companies = check_access(company)
	if parent:
		return get_nodes(company, companies, get_employees(company, {"reports_to": parent}))

	# people whose manager is not in this chart (none, other company, not active) start a branch
	managers = {
		employee.name: employee.reports_to
		for employee in get_employees(company, fields=["name", "reports_to"])
	}
	roots = [name for name, manager in managers.items() if manager not in managers]
	if not roots:
		return []

	return get_nodes(company, companies, get_employees(company, {"name": ["in", roots]}))


@frappe.whitelist()
def get_all_nodes(company: str) -> list[dict]:
	companies = check_access(company)
	if frappe.db.count("Employee", {"company": company, "status": "Active"}) > EXPAND_ALL_LIMIT:
		frappe.throw(
			_(
				"{0} has more than {1} active employees, too many to open at once. Find a person, or open teams one at a time."
			).format(frappe.bold(company), EXPAND_ALL_LIMIT),
			title=_("Too Many Employees"),
		)

	return get_nodes(company, companies, get_employees(company))


@frappe.whitelist()
def get_directory(company: str) -> list[dict]:
	"""Everyone in the company, the top of the chart first"""
	check_access(company)
	employees = get_employees(
		company, fields=[*NODE_FIELDS, "date_of_joining", "date_of_birth"], order_by="lft"
	)
	names = [employee.name for employee in employees]
	leave_status = get_leave_status({name: company for name in names})
	access = get_profile_access(names)
	today = getdate()
	# only whether someone joined recently, not the date
	joined_after = add_days(today, -NEW_JOINER_DAYS)
	# the reminders HR Settings already sends the whole company
	reminders = frappe._dict(
		birthdays=cint(frappe.db.get_single_value("HR Settings", "send_birthday_reminders")),
		anniversaries=cint(frappe.db.get_single_value("HR Settings", "send_work_anniversary_reminders")),
	)

	return [
		frappe._dict(
			get_person(employee, leave_status, access),
			manager=employee.reports_to,
			new_joiner=bool(employee.date_of_joining and getdate(employee.date_of_joining) > joined_after),
			celebrating=get_celebration(employee, today, reminders),
		)
		for employee in employees
	]


def get_celebration(employee: frappe._dict, today: date, reminders: frappe._dict) -> dict | None:
	"""A birthday or work anniversary today, where the reminders announce it anyway. Never the date."""
	if reminders.birthdays and is_anniversary(employee.date_of_birth, today):
		return {"birthday": True}
	if reminders.anniversaries and is_anniversary(employee.date_of_joining, today):
		return {"years": today.year - getdate(employee.date_of_joining).year}
	return None


def is_anniversary(day: date | None, today: date) -> bool:
	if not day:
		return False
	day = getdate(day)
	return (day.month, day.day) == (today.month, today.day) and day.year < today.year


@frappe.whitelist()
def search_employees(company: str, txt: str = "") -> list[dict]:
	"""Matches for "Find a person". With nothing typed, `lft` puts the top of the chart first."""
	check_access(company)
	txt = txt[:SEARCH_TEXT_LIMIT]
	return frappe.get_all(
		"Employee",
		filters={"company": company, "status": "Active"},
		or_filters={"employee_name": ["like", f"%{txt}%"], "name": ["like", f"%{txt}%"]} if txt else None,
		fields=["name", "employee_name", "image", "designation", "department.department_name as department"],
		order_by="employee_name" if txt else "lft",
		limit=SEARCH_LIMIT,
	)


@frappe.whitelist()
def get_path(company: str, employee: str) -> list[str]:
	"""Managers from the top of the chart down to `employee`"""
	check_access(company)
	path = []
	# stop on a reporting loop rather than walk it forever
	while employee and employee not in path:
		found = get_employees(company, {"name": employee}, fields=["reports_to"])
		if not found:
			break
		path.append(employee)
		employee = found[0].reports_to

	return path[::-1]


def get_employees(
	company: str,
	filters: dict | None = None,
	fields: list[str] | None = None,
	order_by: str = "employee_name",
) -> list[frappe._dict]:
	"""Active employees of the company. Callers check access first."""
	return frappe.get_all(
		"Employee",
		filters={"company": company, "status": "Active", **(filters or {})},
		fields=fields or NODE_FIELDS,
		order_by=order_by,
		limit=0,
	)


def get_nodes(company: str, companies: set[str], employees: list[frappe._dict]) -> list[frappe._dict]:
	"""Cards for `employees`. `companies` are the ones the user may see."""
	if not employees:
		return []

	names = [employee.name for employee in employees]
	teams = {}
	for member in get_employees(
		company, {"reports_to": ["in", names]}, fields=["name", "employee_name", "image", "reports_to"]
	):
		teams.setdefault(member.reports_to, []).append(member)

	managers = get_managers({employee.reports_to for employee in employees} - {None, ""})
	# only an active manager in a company the user may see shows more than their name
	visible_managers = {name: manager for name, manager in managers.items() if is_visible(manager, companies)}
	# a manager in another company has that company's holidays
	leave_status = get_leave_status(
		{name: company for name in names}
		| {manager.name: manager.company for manager in visible_managers.values()}
	)
	access = get_profile_access(names + list(visible_managers))

	return [
		frappe._dict(
			get_person(employee, leave_status, access),
			reports=len(teams.get(employee.name, [])),
			team=[
				{"id": member.name, "name": member.employee_name, "image": member.image}
				for member in teams.get(employee.name, [])[:TEAM_PREVIEW_SIZE]
			],
			manager=get_manager_card(managers.get(employee.reports_to), companies, leave_status, access),
		)
		for employee in employees
	]


def get_manager_card(
	manager: frappe._dict | None, companies: set[str], leave_status: dict[str, dict], access: frappe._dict
) -> frappe._dict | None:
	if not manager:
		return None
	if is_visible(manager, companies):
		return frappe._dict(get_person(manager, leave_status, access), company=manager.company)
	return frappe._dict(
		id=manager.name, name=manager.employee_name, image=manager.image, company=manager.company
	)


def is_visible(manager: frappe._dict, companies: set[str]) -> bool:
	return manager.status == "Active" and manager.company in companies


def get_profile_access(names: list[str]) -> frappe._dict:
	"""Whose profile the user may open, and whom desk's composer may email for them.

	Both need permission on the person's Employee record, which a user permission limits.
	"""
	return frappe._dict(
		readable=set(frappe.get_list("Employee", filters={"name": ["in", names]}, pluck="name", limit=0)),
		email=frappe.has_permission("Employee", ptype="email"),
	)


def get_person(employee: frappe._dict, leave_status: dict[str, dict], access: frappe._dict) -> frappe._dict:
	"""One person's card, with their manager's hover card"""
	can_open = employee.name in access.readable
	return frappe._dict(
		id=employee.name,
		name=employee.employee_name,
		image=employee.image,
		designation=employee.designation,
		department=employee.department,
		branch=employee.branch,
		email=employee.company_email,
		leave=leave_status.get(employee.name),
		can_open=can_open,
		can_email=can_open and access.email,
	)


def get_managers(names: set[str]) -> dict[str, frappe._dict]:
	"""Manager of each employee, with their company and status"""
	if not names:
		return {}

	return {
		manager.name: manager
		for manager in frappe.get_all(
			"Employee",
			filters={"name": ["in", list(names)]},
			fields=[*NODE_FIELDS, "company", "status"],
			limit=0,
		)
	}


def get_leave_status(employee_company_map: dict[str, str]) -> dict[str, dict]:
	"""Employees on approved leave today: a half day, or the date they are back.

	Only dates are read, never the leave type or reason.
	"""
	today = getdate()
	lookahead_end = add_days(today, RETURN_LOOKAHEAD_DAYS)

	leaves = {}
	for leave in frappe.get_all(
		"Leave Application",
		filters={
			"employee": ["in", list(employee_company_map)],
			"status": "Approved",
			"docstatus": 1,
			"from_date": ["<=", lookahead_end],
			"to_date": [">=", today],
		},
		fields=["employee", "from_date", "to_date", "half_day", "half_day_date"],
		limit=0,
	):
		leaves.setdefault(leave.employee, []).append(leave)

	on_leave = {
		employee: employee_leaves
		for employee, employee_leaves in leaves.items()
		if get_leave_on(today, employee_leaves)
	}
	if not on_leave:
		return {}

	holidays = get_holidays_in_ranges_map(
		get_holiday_list_ranges_for_employees(
			{employee: employee_company_map[employee] for employee in on_leave},
			add_days(today, 1),
			lookahead_end,
		)
	)

	leave_status = {}
	for employee, employee_leaves in on_leave.items():
		if is_half_day(get_leave_on(today, employee_leaves), today):
			leave_status[employee] = {"half_day": True, "back_on": None}
			continue

		holiday_dates = {holiday.holiday_date for holiday in holidays.get(employee, [])}
		back_on = add_days(today, 1)
		while back_on <= lookahead_end and (
			back_on in holiday_dates or is_on_full_leave(back_on, employee_leaves)
		):
			back_on = add_days(back_on, 1)

		leave_status[employee] = {"half_day": False, "back_on": back_on if back_on <= lookahead_end else None}

	return leave_status


def get_leave_on(day: date, leaves: list[frappe._dict]) -> frappe._dict | None:
	return next((leave for leave in leaves if leave.from_date <= day <= leave.to_date), None)


def is_half_day(leave: frappe._dict, day: date) -> bool:
	return bool(leave.half_day) and (leave.from_date == leave.to_date or leave.half_day_date == day)


def is_on_full_leave(day: date, leaves: list[frappe._dict]) -> bool:
	leave = get_leave_on(day, leaves)
	return bool(leave) and not is_half_day(leave, day)
