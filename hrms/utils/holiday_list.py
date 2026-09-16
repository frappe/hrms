from datetime import date

import frappe
from frappe import _
from frappe.utils import add_days, formatdate, get_link_to_form, getdate


def get_holiday_dates_between(
	holiday_list: str,
	start_date: str,
	end_date: str,
	skip_weekly_offs: bool = False,
	as_dict: bool = False,
	select_weekly_off: bool = False,
) -> list:
	Holiday = frappe.qb.DocType("Holiday")
	query = frappe.qb.from_(Holiday).select(Holiday.holiday_date)

	if select_weekly_off:
		query = query.select(Holiday.weekly_off)

	query = query.where(
		(Holiday.parent == holiday_list) & (Holiday.holiday_date.between(start_date, end_date))
	)

	if skip_weekly_offs:
		query = query.where(Holiday.weekly_off == 0)

	if as_dict:
		return query.run(as_dict=True)

	return query.run(pluck=True)


def get_holiday_dates_between_range(
	assigned_to: str,
	start_date: str,
	end_date: str,
	skip_weekly_offs: bool = False,
	select_weekly_offs: bool = False,
	raise_exception_for_holiday_list: bool = True,
	as_dict: bool = False,
) -> list:
	"""Returns holidays between the dates, honouring holiday list changes within the range"""
	holiday_list_ranges = get_holiday_list_ranges_for_employee(
		assigned_to, start_date, end_date, raise_exception=raise_exception_for_holiday_list
	)
	holidays = get_holidays_in_ranges(holiday_list_ranges, skip_weekly_offs=skip_weekly_offs)

	if as_dict:
		return holidays

	return [holiday.holiday_date for holiday in holidays]


def get_holidays_in_ranges(
	holiday_list_ranges: list[dict], skip_weekly_offs: bool = False
) -> list[frappe._dict]:
	"""Returns holidays falling within the given holiday list ranges in a single query"""
	return get_holidays_in_ranges_map({None: holiday_list_ranges}, skip_weekly_offs).get(None, [])


def get_holidays_in_ranges_map(
	holiday_list_ranges_map: dict[str, list[dict]], skip_weekly_offs: bool = False
) -> dict[str, list[frappe._dict]]:
	"""
	Fetches holidays for many keys (usually employees) in a single query, each restricted to its own
	holiday list ranges.

	{"EMP-001": [{"name", "parent", "holiday_date", "description", "weekly_off"}, ...]}
	"""
	all_ranges = [
		holiday_list_range
		for holiday_list_ranges in holiday_list_ranges_map.values()
		for holiday_list_range in holiday_list_ranges
	]
	if not all_ranges:
		return {}

	Holiday = frappe.qb.DocType("Holiday")
	query = (
		frappe.qb.from_(Holiday)
		.select(Holiday.name, Holiday.parent, Holiday.holiday_date, Holiday.description, Holiday.weekly_off)
		.where(Holiday.parent.isin(list({r["holiday_list"] for r in all_ranges})))
		.where(
			Holiday.holiday_date.between(
				min(getdate(r["from_date"]) for r in all_ranges),
				max(getdate(r["to_date"]) for r in all_ranges),
			)
		)
		.orderby(Holiday.holiday_date)
	)
	if skip_weekly_offs:
		query = query.where(Holiday.weekly_off == 0)

	holidays_by_list = {}
	for holiday in query.run(as_dict=True):
		holidays_by_list.setdefault(holiday.parent, []).append(holiday)

	holidays_map = {}
	for key, holiday_list_ranges in holiday_list_ranges_map.items():
		holidays = [
			holiday
			for holiday_list_range in sorted(holiday_list_ranges, key=lambda r: r["from_date"])
			for holiday in holidays_by_list.get(holiday_list_range["holiday_list"], [])
			if getdate(holiday_list_range["from_date"])
			<= getdate(holiday.holiday_date)
			<= getdate(holiday_list_range["to_date"])
		]
		if holidays:
			holidays_map[key] = holidays

	return holidays_map


def get_holiday_list_ranges_for_employee(
	employee: str,
	start_date: date | str,
	end_date: date | str,
	raise_exception: bool = True,
) -> list[frappe._dict]:
	"""
	Splits [start_date, end_date] into ranges, one per holiday list assigned during it.

	[{"holiday_list": "HL-1", "from_date": date, "to_date": date}, ...]
	"""
	company = frappe.db.get_value("Employee", employee, "company")
	return get_holiday_list_ranges_for_employees(
		{employee: company}, start_date, end_date, raise_exception=raise_exception
	).get(employee, [])


def get_holiday_list_ranges_for_employees(
	employee_company_map: dict[str, str],
	start_date: date | str,
	end_date: date | str,
	raise_exception: bool = False,
) -> dict[str, list[frappe._dict]]:
	"""
	Resolves the holiday list in effect on every date of [start_date, end_date] for many employees,
	fetching all of their and their companies' assignments in a single query. An assignment stays in
	effect until the next assignment starts, exactly as in `get_holiday_list_for_employee`. Dates before
	the employee's first assignment use the company's assignments, and dates before both use the
	earliest assignment.

	{"EMP-001": [{"holiday_list": "HL-1", "from_date": date, "to_date": date}, ...]}
	"""
	if not employee_company_map:
		return {}

	start_date = getdate(start_date)
	end_date = getdate(end_date)
	companies = list({company for company in employee_company_map.values() if company})

	assignments = get_holiday_list_assignments(list(employee_company_map) + companies)
	effective_ranges = build_effective_date_ranges_for_holiday_assignments(assignments, start_date, end_date)

	employee_holiday_list_ranges = {}
	for employee, company in employee_company_map.items():
		ranges = fill_employee_holiday_list_date_gaps_with_company_holiday_list(
			effective_ranges.get(employee, []), effective_ranges.get(company, []), start_date, end_date
		)
		ranges = fill_uncovered_dates_with_assigned_holiday_list(
			ranges, assignments.get(employee, []), assignments.get(company, []), start_date, end_date
		)

		if ranges:
			employee_holiday_list_ranges[employee] = ranges
		elif raise_exception:
			throw_no_holiday_list_assigned(employee, company, start_date)

	return employee_holiday_list_ranges


def fill_uncovered_dates_with_assigned_holiday_list(
	ranges: list[dict],
	employee_assignments: list[dict],
	company_assignments: list[dict],
	start_date: date,
	end_date: date,
) -> list[frappe._dict]:
	"""
	Dates before the first assignment resolve like a single date would. Adjacent ranges using the
	same holiday list are merged.
	"""
	filled = []

	def add_range(holiday_list, from_date, to_date):
		last = filled[-1] if filled else None
		if last and last.holiday_list == holiday_list and add_days(last.to_date, 1) == from_date:
			last.to_date = to_date
		else:
			filled.append(frappe._dict(holiday_list=holiday_list, from_date=from_date, to_date=to_date))

	current = start_date
	for holiday_list_range in [*sorted(ranges, key=lambda r: r["from_date"]), None]:
		gap_end = add_days(holiday_list_range["from_date"], -1) if holiday_list_range else end_date
		if current <= gap_end:
			assignment = resolve_holiday_list_assignment(employee_assignments, company_assignments, current)
			if assignment:
				add_range(assignment.holiday_list, current, gap_end)

		if holiday_list_range:
			add_range(
				holiday_list_range["holiday_list"],
				getdate(holiday_list_range["from_date"]),
				getdate(holiday_list_range["to_date"]),
			)
			current = add_days(holiday_list_range["to_date"], 1)

	return filled


def resolve_holiday_list_assignment(
	employee_assignments: list[dict], company_assignments: list[dict], as_on: date
) -> frappe._dict | None:
	"""
	Latest assignment starting on or before `as_on`, employee first and company second.
	Dates before the first assignment fall back to the earliest one.
	"""
	for assignments in (employee_assignments, company_assignments):
		active = [a for a in assignments if getdate(a.from_date) <= as_on]
		if active:
			return active[-1]

	for assignments in (employee_assignments, company_assignments):
		if assignments:
			return assignments[0]

	return None


def get_holiday_list_assignments(assigned_to_list: list[str]) -> dict[str, list[frappe._dict]]:
	"""Submitted assignments of the given employees and companies, ordered by from_date"""
	assigned_to_list = [assigned_to for assigned_to in assigned_to_list if assigned_to]
	if not assigned_to_list:
		return {}

	HLA = frappe.qb.DocType("Holiday List Assignment")
	assignments = (
		frappe.qb.from_(HLA)
		.select(HLA.assigned_to, HLA.holiday_list, HLA.from_date)
		.where(HLA.assigned_to.isin(assigned_to_list))
		.where(HLA.docstatus == 1)
		.orderby(HLA.assigned_to)
		.orderby(HLA.from_date)
	).run(as_dict=True)

	assignment_map = {}
	for assignment in assignments:
		assignment_map.setdefault(assignment.assigned_to, []).append(assignment)

	return assignment_map


def get_holiday_list_for_employee(
	employee: str, raise_exception: bool = True, as_on: date | str | None = None, as_dict: bool = False
) -> str:
	as_on = getdate(as_on)
	company = frappe.db.get_value("Employee", employee, "company")
	assignments = get_holiday_list_assignments([employee, company])
	assignment = resolve_holiday_list_assignment(
		assignments.get(employee, []), assignments.get(company, []), as_on
	)

	if not assignment:
		if raise_exception:
			throw_no_holiday_list_assigned(employee, company, as_on)
		return None

	if as_dict:
		return frappe._dict(holiday_list=assignment.holiday_list, from_date=assignment.from_date)

	return assignment.holiday_list


def throw_no_holiday_list_assigned(employee: str, company: str, as_on: date):
	frappe.throw(
		_(
			"No Holiday List was found for Employee {0} or their company {1} for date {2}. Please assign through {3}"
		).format(
			frappe.bold(employee),
			frappe.bold(company),
			frappe.bold(formatdate(as_on)),
			get_link_to_form("Holiday List Assignment", label="Holiday List Assignment"),
		)
	)


def get_assigned_holiday_list(assigned_to: str, as_on=None, as_dict: bool = False) -> str:
	"""Holiday list assigned directly to the employee or company on `as_on`"""
	as_on = getdate(as_on)
	assignments = get_holiday_list_assignments([assigned_to]).get(assigned_to, [])
	active = [a for a in assignments if getdate(a.from_date) <= as_on]
	if not active:
		return None

	assignment = active[-1]
	if as_dict:
		return frappe._dict(holiday_list=assignment.holiday_list, from_date=assignment.from_date)

	return assignment.holiday_list


def build_effective_date_ranges_for_holiday_assignments(
	holiday_assignment_map: dict[str, list[dict]],
	start_date: date,
	end_date: date,
) -> dict[str, list[dict]]:
	"""
	Returns map of {assigned_to: [{"holiday_list", "from_date", "to_date"}]} clipped to [start_date, end_date].
	Each assignment stays in effect until the day before the next assignment starts.
	"""
	result = {}
	for assigned_to, assignments in holiday_assignment_map.items():
		ranges = []
		for idx, assignment in enumerate(assignments):
			next_assignment = assignments[idx + 1] if idx + 1 < len(assignments) else None
			effective_to_date = add_days(next_assignment.from_date, -1) if next_assignment else end_date

			from_date = max(getdate(assignment.from_date), start_date)
			effective_to_date = min(getdate(effective_to_date), end_date)

			if from_date <= effective_to_date:
				ranges.append(
					{
						"holiday_list": assignment.holiday_list,
						"from_date": from_date,
						"to_date": effective_to_date,
					}
				)
		if ranges:
			result[assigned_to] = ranges

	return result


def fill_employee_holiday_list_date_gaps_with_company_holiday_list(
	primary_ranges: list[dict],
	fallback_ranges: list[dict],
	start_date: date,
	end_date: date,
) -> list[dict]:
	"""
	For any dates in [start_date, end_date] not covered by primary_ranges,
	fills those gaps using fallback_ranges (typically company assignments).

	Example: employee HLA starts Jan 16, company HLA covers full month →
	Jan 1-15 use the company holiday list, Jan 16-31 use the employee's.
	"""
	if not primary_ranges:
		return fallback_ranges
	if not fallback_ranges:
		return primary_ranges

	result = []
	current = start_date

	for primary in sorted(primary_ranges, key=lambda r: r["from_date"]):
		gap_end = add_days(primary["from_date"], -1)
		if current <= gap_end:
			for fallback in fallback_ranges:
				overlap_start = max(getdate(fallback["from_date"]), current)
				overlap_end = min(getdate(fallback["to_date"]), gap_end)
				if overlap_start <= overlap_end:
					result.append(
						{
							"holiday_list": fallback["holiday_list"],
							"from_date": overlap_start,
							"to_date": overlap_end,
						}
					)
		result.append(primary)
		current = add_days(primary["to_date"], 1)

	if current <= end_date:
		for fallback in fallback_ranges:
			overlap_start = max(getdate(fallback["from_date"]), current)
			overlap_end = min(getdate(fallback["to_date"]), end_date)
			if overlap_start <= overlap_end:
				result.append(
					{
						"holiday_list": fallback["holiday_list"],
						"from_date": overlap_start,
						"to_date": overlap_end,
					}
				)

	return sorted(result, key=lambda r: r["from_date"])


def clip_holiday_list_ranges(holiday_list_ranges: list[dict], start_date: date, end_date: date) -> list[dict]:
	"""Restricts the ranges to [start_date, end_date]"""
	clipped = []
	for holiday_list_range in holiday_list_ranges:
		from_date = max(getdate(holiday_list_range["from_date"]), getdate(start_date))
		to_date = min(getdate(holiday_list_range["to_date"]), getdate(end_date))
		if from_date <= to_date:
			clipped.append(
				frappe._dict(
					holiday_list=holiday_list_range["holiday_list"], from_date=from_date, to_date=to_date
				)
			)

	return clipped


def invalidate_cache(doc, method=None):
	from hrms.payroll.doctype.salary_slip.salary_slip import HOLIDAYS_BETWEEN_DATES

	frappe.cache().delete_value(HOLIDAYS_BETWEEN_DATES)
