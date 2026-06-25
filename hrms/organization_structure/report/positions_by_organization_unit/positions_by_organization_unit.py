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
			"label": _("Organization Unit"),
			"fieldname": "organization_unit",
			"fieldtype": "Link",
			"options": "Organization Unit",
			"width": 280,
		},
		{"label": _("Unit Type"), "fieldname": "unit_type", "fieldtype": "Data", "width": 140},
		{"label": _("Total Positions"), "fieldname": "total_positions", "fieldtype": "Int", "width": 130},
		{"label": _("Occupied"), "fieldname": "occupied", "fieldtype": "Int", "width": 110},
		{"label": _("Vacant"), "fieldname": "vacant", "fieldtype": "Int", "width": 110},
		{"label": _("Occupancy %"), "fieldname": "occupancy_rate", "fieldtype": "Percent", "width": 120},
	]


def get_data(filters):
	position_filters = {}
	if filters.get("unit_type"):
		units = frappe.get_all(
			"Organization Unit", filters={"unit_type": filters.unit_type}, pluck="name"
		)
		position_filters["organization_unit"] = ["in", units or [""]]

	positions = frappe.get_all(
		"Position",
		filters=position_filters,
		fields=["organization_unit", "is_occupied"],
	)

	summary = {}
	for position in positions:
		row = summary.setdefault(
			position.organization_unit, {"total_positions": 0, "occupied": 0, "vacant": 0}
		)
		row["total_positions"] += 1
		if position.is_occupied:
			row["occupied"] += 1
		else:
			row["vacant"] += 1

	unit_types = dict(
		frappe.get_all("Organization Unit", fields=["name", "unit_type"], as_list=True)
	)

	data = []
	for unit, row in sorted(summary.items()):
		total = row["total_positions"]
		row.update(
			{
				"organization_unit": unit,
				"unit_type": unit_types.get(unit),
				"occupancy_rate": (row["occupied"] / total * 100) if total else 0,
			}
		)
		data.append(row)

	return data
