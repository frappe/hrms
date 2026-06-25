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
			"label": _("Woreda"),
			"fieldname": "woreda",
			"fieldtype": "Link",
			"options": "Woreda",
			"width": 220,
		},
		{
			"label": _("City"),
			"fieldname": "city",
			"fieldtype": "Link",
			"options": "City",
			"width": 220,
		},
		{"label": _("Total Branches"), "fieldname": "total_branches", "fieldtype": "Int", "width": 130},
		{"label": _("Active Branches"), "fieldname": "active_branches", "fieldtype": "Int", "width": 130},
		{"label": _("Inactive Branches"), "fieldname": "inactive_branches", "fieldtype": "Int", "width": 140},
	]


def get_data(filters):
	conditions = {"location_1": "Branch"}
	if filters.get("city"):
		conditions["city"] = filters.city

	branches = frappe.get_all(
		"Organization Unit",
		filters=conditions,
		fields=["woreda", "city", "status"],
	)

	summary = {}
	for branch in branches:
		key = (branch.woreda or "", branch.city or "")
		row = summary.setdefault(
			key, {"total_branches": 0, "active_branches": 0, "inactive_branches": 0}
		)
		row["total_branches"] += 1
		if branch.status == "Active":
			row["active_branches"] += 1
		elif branch.status == "Inactive":
			row["inactive_branches"] += 1

	data = []
	for (woreda, city), row in sorted(summary.items()):
		row.update({"woreda": woreda or None, "city": city or None})
		data.append(row)

	return data
