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
			"label": _("Region"),
			"fieldname": "region",
			"fieldtype": "Link",
			"options": "Region",
			"width": 260,
		},
		{"label": _("Total Branches"), "fieldname": "total_branches", "fieldtype": "Int", "width": 130},
		{"label": _("Active Branches"), "fieldname": "active_branches", "fieldtype": "Int", "width": 130},
		{"label": _("Inactive Branches"), "fieldname": "inactive_branches", "fieldtype": "Int", "width": 140},
	]


def get_data(filters):
	branches = frappe.get_all(
		"Organization Unit",
		filters={"location_1": "Branch"},
		fields=["region", "status"],
	)

	summary = {}
	for branch in branches:
		key = branch.region or ""
		row = summary.setdefault(
			key, {"total_branches": 0, "active_branches": 0, "inactive_branches": 0}
		)
		row["total_branches"] += 1
		if branch.status == "Active":
			row["active_branches"] += 1
		elif branch.status == "Inactive":
			row["inactive_branches"] += 1

	data = []
	for region, row in sorted(summary.items()):
		row["region"] = region or None
		data.append(row)

	return data
