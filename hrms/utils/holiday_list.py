import frappe


def get_holiday_dates_between(holiday_list: str, start_date: str, end_date: str) -> list:
	Holiday = frappe.qb.DocType("Holiday")
	return (
		frappe.qb.from_(Holiday)
		.select(Holiday.holiday_date)
		.where((Holiday.parent == holiday_list) & (Holiday.holiday_date.between(start_date, end_date)))
		.orderby(Holiday.holiday_date)
	).run(pluck=True)
