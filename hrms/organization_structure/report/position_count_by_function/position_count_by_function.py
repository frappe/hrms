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
			"label": _("Function"),
			"fieldname": "function",
			"fieldtype": "Link",
			"options": "Organization Unit",
			"width": 280,
		},
		{"label": _("Total Positions"), "fieldname": "total_positions", "fieldtype": "Int", "width": 140},
		{"label": _("Occupied"), "fieldname": "occupied", "fieldtype": "Int", "width": 120},
		{"label": _("Vacant"), "fieldname": "vacant", "fieldtype": "Int", "width": 120},
	]


def get_data(filters):
	functions = frappe.get_all(
		"Organization Unit",
		filters={"unit_type": "Function"},
		fields=["name", "lft", "rgt"],
		order_by="lft asc",
	)

	unit_lft = {
		u.name: cint(u.lft)
		for u in frappe.get_all("Organization Unit", fields=["name", "lft"])
	}

	positions = frappe.get_all("Position", fields=["organization_unit", "is_occupied"])

	summary = {fn.name: {"total_positions": 0, "occupied": 0, "vacant": 0} for fn in functions}
	summary["Unassigned"] = {"total_positions": 0, "occupied": 0, "vacant": 0}

	for position in positions:
		pos_lft = unit_lft.get(position.organization_unit)
		bucket = "Unassigned"

		if pos_lft is not None:
			# nearest enclosing function = function with greatest lft whose range contains the unit
			enclosing = [f for f in functions if cint(f.lft) <= pos_lft <= cint(f.rgt)]
			if enclosing:
				bucket = max(enclosing, key=lambda f: cint(f.lft)).name

		row = summary[bucket]
		row["total_positions"] += 1
		if position.is_occupied:
			row["occupied"] += 1
		else:
			row["vacant"] += 1

	data = []
	for function, row in summary.items():
		if not row["total_positions"]:
			continue
		row["function"] = function
		data.append(row)

	return data
