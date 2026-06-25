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
			"label": _("Position"),
			"fieldname": "position",
			"fieldtype": "Link",
			"options": "Position",
			"width": 260,
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
			"width": 180,
		},
		{
			"label": _("Job Grade"),
			"fieldname": "job_grade",
			"fieldtype": "Link",
			"options": "Job Grade",
			"width": 150,
		},
		{"label": _("Level"), "fieldname": "position_level", "fieldtype": "Int", "width": 80},
		{
			"label": _("Reports To"),
			"fieldname": "parent_position",
			"fieldtype": "Link",
			"options": "Position",
			"width": 220,
		},
	]


def get_data(filters):
	conditions = {"is_occupied": 0}
	# default to active positions unless explicitly overridden
	conditions["position_status"] = filters.get("position_status") or "Active"

	if filters.get("organization_unit"):
		conditions["organization_unit"] = filters.organization_unit
	if filters.get("site_organization_unit"):
		conditions["site_organization_unit"] = filters.site_organization_unit
	if filters.get("job_grade"):
		conditions["job_grade"] = filters.job_grade

	return frappe.get_all(
		"Position",
		filters=conditions,
		fields=[
			"name as position",
			"position_code",
			"organization_unit",
			"site_organization_unit",
			"job_grade",
			"position_level",
			"parent_position",
		],
		order_by="position_level asc, position_name asc",
	)
