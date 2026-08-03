# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from frappe.utils import date_diff, getdate, today
from frappe.utils.dashboard import cache_source


@frappe.whitelist()
@cache_source
def get_data(
	chart_name: str | None = None,
	chart: str | None = None,
	no_cache: str | None = None,
	filters: str | None = None,
	from_date: str | None = None,
	to_date: str | None = None,
	timespan: str | None = None,
	time_interval: str | None = None,
	heatmap_year: str | None = None,
) -> dict[str, list]:
	if filters:
		filters = frappe.parse_json(filters)
	else:
		filters = {}

	company = filters.get("company")

	opening_filters = {"status": "Open", "docstatus": ["!=", 2]}
	if company:
		opening_filters["company"] = company

	openings = frappe.get_all(
		"Job Opening",
		filters=opening_filters,
		fields=["name", "job_title", "posted_on"],
	)

	today_date = getdate(today())

	rows = []
	for opening in openings:
		if not opening.posted_on:
			continue
		age = date_diff(today_date, getdate(opening.posted_on))
		label = opening.job_title or opening.name
		rows.append((label, age))

	rows.sort(key=lambda r: r[1], reverse=True)
	rows = rows[:10]

	labels = [r[0] for r in rows]
	values = [r[1] for r in rows]

	return {
		"labels": labels,
		"datasets": [{"name": _("Days Open"), "values": values}],
	}
