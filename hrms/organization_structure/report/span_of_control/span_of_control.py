# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{
			"label": _("Position"),
			"fieldname": "position",
			"fieldtype": "Link",
			"options": "Position",
			"width": 280,
		},
		{
			"label": _("Organization Unit"),
			"fieldname": "organization_unit",
			"fieldtype": "Link",
			"options": "Organization Unit",
			"width": 200,
		},
		{"label": _("Level"), "fieldname": "position_level", "fieldtype": "Int", "width": 80},
		{"label": _("Direct Reports"), "fieldname": "direct_reports", "fieldtype": "Int", "width": 130},
		{"label": _("Total Reports"), "fieldname": "total_reports", "fieldtype": "Int", "width": 130},
	]


def get_data(filters):
	conditions = {}
	if filters.get("only_managers"):
		conditions["is_group"] = 1

	positions = frappe.get_all(
		"Position",
		filters=conditions,
		fields=["name", "organization_unit", "position_level", "lft", "rgt"],
		order_by="position_level asc, position_name asc",
	)

	# direct reports per parent
	direct_counts = {}
	for row in frappe.get_all(
		"Position",
		filters={"parent_position": ["is", "set"]},
		fields=["parent_position", "count(name) as count"],
		group_by="parent_position",
	):
		direct_counts[row.parent_position] = row.count

	data = []
	for position in positions:
		# total descendants via nested set: (rgt - lft - 1) / 2
		total_reports = max((cint(position.rgt) - cint(position.lft) - 1) // 2, 0)
		direct_reports = direct_counts.get(position.name, 0)

		if filters.get("hide_leaf_positions") and not direct_reports:
			continue

		data.append(
			{
				"position": position.name,
				"organization_unit": position.organization_unit,
				"position_level": position.position_level,
				"direct_reports": direct_reports,
				"total_reports": total_reports,
			}
		)

	return data
