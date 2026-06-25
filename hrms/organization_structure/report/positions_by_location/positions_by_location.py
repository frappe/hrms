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
			"label": _("Site Organization Unit"),
			"fieldname": "site_organization_unit",
			"fieldtype": "Link",
			"options": "Organization Unit",
			"width": 280,
		},
		{"label": _("Location"), "fieldname": "location_1", "fieldtype": "Data", "width": 140},
		{"label": _("Total Positions"), "fieldname": "total_positions", "fieldtype": "Int", "width": 130},
		{"label": _("Occupied"), "fieldname": "occupied", "fieldtype": "Int", "width": 110},
		{"label": _("Vacant"), "fieldname": "vacant", "fieldtype": "Int", "width": 110},
		{"label": _("Occupancy %"), "fieldname": "occupancy_rate", "fieldtype": "Percent", "width": 120},
	]


def get_data(filters):
	location_filters = {}
	if filters.get("location_1"):
		location_filters["location_1"] = filters.location_1

	location_types = {
		loc.name: loc.location_1
		for loc in frappe.get_all(
			"Organization Unit", filters=location_filters, fields=["name", "location_1"]
		)
	}

	position_filters = {"site_organization_unit": ["is", "set"]}
	if filters.get("location_1"):
		position_filters["site_organization_unit"] = ["in", list(location_types.keys()) or [""]]

	positions = frappe.get_all(
		"Position",
		filters=position_filters,
		fields=["site_organization_unit", "is_occupied"],
	)

	summary = {}
	for position in positions:
		row = summary.setdefault(
			position.site_organization_unit, {"total_positions": 0, "occupied": 0, "vacant": 0}
		)
		row["total_positions"] += 1
		if position.is_occupied:
			row["occupied"] += 1
		else:
			row["vacant"] += 1

	data = []
	for location, row in sorted(summary.items()):
		total = row["total_positions"]
		row.update(
			{
				"site_organization_unit": location,
				"location_1": location_types.get(location),
				"occupancy_rate": (row["occupied"] / total * 100) if total else 0,
			}
		)
		data.append(row)

	return data
