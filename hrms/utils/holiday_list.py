import frappe
from frappe import _


def get_holiday_dates_between(
	holiday_list: str,
	start_date: str,
	end_date: str,
	skip_weekly_offs: bool = False,
) -> list:
	Holiday = frappe.qb.DocType("Holiday")
	query = (
		frappe.qb.from_(Holiday)
		.select(Holiday.holiday_date)
		.where((Holiday.parent == holiday_list) & (Holiday.holiday_date.between(start_date, end_date)))
		.orderby(Holiday.holiday_date)
	)

	if skip_weekly_offs:
		query = query.where(Holiday.weekly_off == 0)

	return query.run(pluck=True)


def invalidate_cache(doc, method=None):
	from hrms.payroll.doctype.salary_slip.salary_slip import HOLIDAYS_BETWEEN_DATES

	frappe.cache().delete_value(HOLIDAYS_BETWEEN_DATES)


def get_holiday_list_for_employee(
	employee: str,
	raise_exception: bool = True,
	as_on=None
) -> str:
	as_on = frappe.utils.getdate(as_on)
	HolidayList = frappe.qb.DocType("Holiday Assignment")
	query = (
		frappe.qb.from_(HolidayList)
		.select(HolidayList.holiday_list)
		.where(HolidayList.employee == employee)
		.where(HolidayList.from_date <= as_on)
		.where(HolidayList.to_date >= as_on)
		.where(HolidayList.docstatus == 1)
		.run()
	)
	holiday_list = query[0][0] if query else None

	if not holiday_list and raise_exception:
		frappe.throw(
			_("Please assign Holiday List for Employee {0}").format(employee)
		)

	return holiday_list
