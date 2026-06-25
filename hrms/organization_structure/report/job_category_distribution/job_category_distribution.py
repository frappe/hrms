# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{
			"label": _("Job Category"),
			"fieldname": "job_category",
			"fieldtype": "Link",
			"options": "Job Category",
			"width": 260,
		},
		{"label": _("Total Positions"), "fieldname": "total_positions", "fieldtype": "Int", "width": 130},
		{"label": _("Occupied"), "fieldname": "occupied", "fieldtype": "Int", "width": 110},
		{"label": _("Vacant"), "fieldname": "vacant", "fieldtype": "Int", "width": 110},
	]


def get_data(filters):
	positions = frappe.get_all("Position", fields=["job_category", "is_occupied"])

	summary = {}
	for position in positions:
		key = position.job_category or _("Unassigned")
		row = summary.setdefault(key, {"total_positions": 0, "occupied": 0, "vacant": 0})
		row["total_positions"] += 1
		if position.is_occupied:
			row["occupied"] += 1
		else:
			row["vacant"] += 1

	data = []
	for category_name, row in summary.items():
		row["job_category"] = category_name
		data.append(row)

	data.sort(key=lambda r: r.get("job_category") or "")
	return data
