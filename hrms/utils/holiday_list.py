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
) -> list:
	start_date = getdate(start_date)
	end_date = getdate(end_date)

	from_holiday_list = (
		get_holiday_list_for_employee(
			assigned_to, as_on=start_date, as_dict=True, raise_exception=raise_exception_for_holiday_list
		)
		or {}
	)
	to_holiday_list = (
		get_holiday_list_for_employee(
			assigned_to, as_on=end_date, as_dict=True, raise_exception=raise_exception_for_holiday_list
		)
		or {}
	)

	if (
		from_holiday_list
		and to_holiday_list
		and from_holiday_list.holiday_list != to_holiday_list.holiday_list
	):
		return list(
			set(
				get_holiday_dates_between(
					holiday_list=from_holiday_list.holiday_list,
					start_date=start_date,
					end_date=add_days(to_holiday_list.from_date, -1),
					select_weekly_off=select_weekly_offs,
					skip_weekly_offs=skip_weekly_offs,
				)
				+ get_holiday_dates_between(
					holiday_list=to_holiday_list.holiday_list,
					start_date=to_holiday_list.from_date,
					end_date=end_date,
					select_weekly_off=select_weekly_offs,
					skip_weekly_offs=skip_weekly_offs,
				)
			)
		)
	elif holiday_list := from_holiday_list.get("holiday_list", None) or to_holiday_list.get(
		"holiday_list", None
	):
		return get_holiday_dates_between(
			holiday_list=holiday_list,
			start_date=start_date,
			end_date=end_date,
			select_weekly_off=select_weekly_offs,
			skip_weekly_offs=skip_weekly_offs,
		)
	else:
		return []


def get_holiday_list_for_employee(
	employee: str, raise_exception: bool = True, as_on: date | str | None = None, as_dict: bool = False
) -> str:
	as_on = frappe.utils.getdate(as_on)
	holiday_list = get_assigned_holiday_list(employee, as_on, as_dict)
	if not holiday_list:
		company = frappe.db.get_value("Employee", employee, "company")
		holiday_list = get_assigned_holiday_list(company, as_on, as_dict)

	if not holiday_list and raise_exception:
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
	return holiday_list


def get_assigned_holiday_list(assigned_to: str, as_on=None, as_dict: bool = False) -> str:
	as_on = frappe.utils.getdate(as_on)
	HLA = frappe.qb.DocType("Holiday List Assignment")
	query = (
		frappe.qb.from_(HLA)
		.select(HLA.holiday_list)
		.where(HLA.assigned_to == assigned_to)
		.where(HLA.from_date <= as_on)
		.where(HLA.docstatus == 1)
		.orderby(HLA.from_date, order=frappe.qb.desc)
		.limit(1)
	)
	if as_dict:
		query = query.select(HLA.from_date)
		holiday_list = query.run(as_dict=True)
		return holiday_list[0] if holiday_list else None

	result = query.run()
	holiday_list = result[0][0] if result else None

	return holiday_list


def get_assigned_holiday_lists_to_employee_and_company(
	assigned_to_list: list[str],
	start_date: date | str,
	end_date: date | str,
) -> dict[str, list[dict]]:
	"""
	Returns effective holiday list ranges for multiple assigned_to values (employees/companies) in one query.

	{
	    "EMP-001": [{"holiday_list": "HL-1", "from_date": date, "to_date": date}, ...],
	    "EMP-002": [...],
	}
	"""
	if not assigned_to_list:
		return {}

	start_date = getdate(start_date)
	end_date = getdate(end_date)

	return build_holiday_list_map(assigned_to_list, start_date, end_date)


def build_holiday_list_map(
	assigned_to_list: list[str],
	start_date: date,
	end_date: date,
) -> dict[str, list[dict]]:
	"""
	Single query + compute effective HLA ranges per assigned_to, clipped to start_date/end_date.
	effective_to_date = MIN(HL.to_date, next assignment's from_date - 1 day)

	{
	    "EMP-001": [{"holiday_list": "HL-1", "from_date": date, "to_date": date}, ...],
	}
	"""
	HLA = frappe.qb.DocType("Holiday List Assignment")
	HolidayList = frappe.qb.DocType("Holiday List")

	holiday_list_assignments = (
		frappe.qb.from_(HLA)
		.join(HolidayList)
		.on(HLA.holiday_list == HolidayList.name)
		.select(
			HLA.assigned_to,
			HLA.holiday_list,
			HLA.from_date,
			HolidayList.to_date.as_("holiday_list_to_date"),
		)
		.where(HLA.assigned_to.isin(assigned_to_list))
		.where(HLA.docstatus == 1)
		.where(HLA.from_date <= end_date)
		.where(HolidayList.to_date >= start_date)
		.orderby(HLA.assigned_to)
		.orderby(HLA.from_date)
	).run(as_dict=True)

	holiday_assignment_map = {}
	for assignment in holiday_list_assignments:
		holiday_assignment_map.setdefault(assignment.assigned_to, []).append(assignment)

	result = build_effective_date_ranges_for_holiday_assignments(holiday_assignment_map, start_date, end_date)

	return result


def build_effective_date_ranges_for_holiday_assignments(
	holiday_assignment_map: dict[str, list[dict]],
	start_date: date,
	end_date: date,
) -> dict[str, list[dict]]:
	"""
	Returns map of {assigned_to: [raw_holiday_list_assignment_rows]},
	effective_to_date = MIN(HL.to_date, next assignment's from_date - 1 day)
	"""
	result = {}
	for assigned_to, assignments in holiday_assignment_map.items():
		ranges = []
		for idx, assignment in enumerate(assignments):
			hl_to_date = getdate(assignment.holiday_list_to_date)
			next_assignment = assignments[idx + 1] if idx + 1 < len(assignments) else None

			if next_assignment:
				effective_to_date = min(hl_to_date, add_days(next_assignment.from_date, -1))
			else:
				effective_to_date = hl_to_date

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


def invalidate_cache(doc, method=None):
	from hrms.payroll.doctype.salary_slip.salary_slip import HOLIDAYS_BETWEEN_DATES

	frappe.cache().delete_value(HOLIDAYS_BETWEEN_DATES)
