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


def invalidate_cache(doc, method=None):
	from hrms.payroll.doctype.salary_slip.salary_slip import HOLIDAYS_BETWEEN_DATES

	frappe.cache().delete_value(HOLIDAYS_BETWEEN_DATES)
