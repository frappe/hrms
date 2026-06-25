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
			"label": _("Organization Unit"),
			"fieldname": "organization_unit",
			"fieldtype": "Link",
			"options": "Organization Unit",
			"width": 320,
		},
		{"label": _("Code"), "fieldname": "unit_code", "fieldtype": "Data", "width": 120},
		{"label": _("Type"), "fieldname": "unit_type", "fieldtype": "Data", "width": 130},
		{"label": _("Level"), "fieldname": "organization_level", "fieldtype": "Int", "width": 80},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
		{
			"label": _("Parent Unit"),
			"fieldname": "parent_organization_unit",
			"fieldtype": "Link",
			"options": "Organization Unit",
			"width": 220,
		},
	]


def get_data(filters):
	conditions = {}
	if filters.get("status"):
		conditions["status"] = filters.status
	if filters.get("unit_type"):
		conditions["unit_type"] = filters.unit_type

	units = frappe.get_all(
		"Organization Unit",
		filters=conditions,
		fields=[
			"name as organization_unit",
			"unit_code",
			"unit_type",
			"organization_level",
			"status",
			"parent_organization_unit",
		],
		order_by="lft asc",
	)

	for unit in units:
		unit["indent"] = max(cint(unit.organization_level) - 1, 0)

	return units
