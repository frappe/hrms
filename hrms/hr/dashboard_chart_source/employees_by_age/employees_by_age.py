# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


from dateutil.relativedelta import relativedelta

import frappe
from frappe import _
from frappe.utils import getdate
from frappe.utils.dashboard import cache_source


@frappe.whitelist()
@cache_source
def get_data(
	chart_name=None,
	chart=None,
	no_cache=None,
	filters=None,
	from_date=None,
	to_date=None,
	timespan=None,
	time_interval=None,
	heatmap_year=None,
) -> dict[str, list]:
	if filters:
		filters = frappe.parse_json(filters)

	employees = frappe.db.get_list(
		"Employee",
		filters={"company": filters.get("company"), "status": "Active"},
		pluck="date_of_birth",
	)
	age_list = get_age_list(employees)
	ranges = get_ranges()

	age_range, values = get_employees_by_age(age_list, ranges)

	return {
		"labels": age_range,
		"datasets": [
			{"name": _("Employees"), "values": values},
		],
	}


def get_ranges() -> list[tuple[int, int]]:
	ranges = []

	for i in range(15, 80, 5):
		ranges.append((i, i + 4))

	ranges.append(80)

	return ranges


def get_age_list(employees) -> list[int]:
	age_list = []
	for dob in employees:
		if not dob:
			continue
		age = relativedelta(getdate(), getdate(dob)).years
		age_list.append(age)

	return age_list


def get_employees_by_age(age_list, ranges) -> tuple[list[str], list[int]]:
	age_range = []
	values = []
	for bracket in ranges:
		if isinstance(bracket, int):
			age_range.append(f"{bracket}+")
		else:
			age_range.append(f"{bracket[0]}-{bracket[1]}")

		count = 0
		for age in age_list:
			if (isinstance(bracket, int) and age >= bracket) or (
				isinstance(bracket, tuple) and bracket[0] <= age <= bracket[1]
			):
				count += 1

		values.append(count)

	return age_range, values
