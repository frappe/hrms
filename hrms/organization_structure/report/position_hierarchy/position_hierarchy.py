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
			"width": 320,
		},
		{"label": _("Code"), "fieldname": "position_code", "fieldtype": "Data", "width": 130},
		{
			"label": _("Organization Unit"),
			"fieldname": "organization_unit",
			"fieldtype": "Link",
			"options": "Organization Unit",
			"width": 180,
		},
		{
			"label": _("Site Organization Unit"),
			"fieldname": "site_organization_unit",
			"fieldtype": "Link",
			"options": "Organization Unit",
			"width": 160,
		},
		{
			"label": _("Job Grade"),
			"fieldname": "job_grade",
			"fieldtype": "Link",
			"options": "Job Grade",
			"width": 130,
		},
		{"label": _("Level"), "fieldname": "position_level", "fieldtype": "Int", "width": 70},
		{
			"label": _("Occupancy"),
			"fieldname": "occupancy_status",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": _("Current Employee"),
			"fieldname": "current_employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 160,
		},
		{"label": _("Status"), "fieldname": "position_status", "fieldtype": "Data", "width": 90},
		{
			"label": _("Reports To"),
			"fieldname": "parent_position",
			"fieldtype": "Link",
			"options": "Position",
			"width": 220,
		},
	]


def get_data(filters):
	conditions = {}
	if filters.get("position_status"):
		conditions["position_status"] = filters.position_status
	if filters.get("organization_unit"):
		conditions["organization_unit"] = filters.organization_unit
	if filters.get("site_organization_unit"):
		conditions["site_organization_unit"] = filters.site_organization_unit
	if filters.get("job_grade"):
		conditions["job_grade"] = filters.job_grade

	positions = frappe.get_all(
		"Position",
		filters=conditions,
		fields=[
			"name as position",
			"position_code",
			"organization_unit",
			"site_organization_unit",
			"job_grade",
			"position_level",
			"occupancy_status",
			"current_employee",
			"position_status",
			"parent_position",
		],
		order_by="lft asc",
	)

	for position in positions:
		position["indent"] = max(cint(position.position_level) - 1, 0)

	return positions
