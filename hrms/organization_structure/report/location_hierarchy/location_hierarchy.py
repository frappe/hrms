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

			"fieldname": "unit_name",

			"fieldtype": "Link",

			"options": "Organization Unit",

			"width": 320,

		},

		{"label": _("Code"), "fieldname": "unit_code", "fieldtype": "Data", "width": 120},

		{"label": _("Location"), "fieldname": "location_1", "fieldtype": "Data", "width": 130},

		{"label": _("Level"), "fieldname": "organization_level", "fieldtype": "Int", "width": 80},

		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},

		{

			"label": _("Parent Organization Unit"),

			"fieldname": "parent_organization_unit",

			"fieldtype": "Link",

			"options": "Organization Unit",

			"width": 220,

		},

		{

			"label": _("Region"),

			"fieldname": "region",

			"fieldtype": "Link",

			"options": "Region",

			"width": 180,

		},

		{

			"label": _("City"),

			"fieldname": "city",

			"fieldtype": "Link",

			"options": "City",

			"width": 180,

		},

	]





def get_data(filters):

	conditions = {}

	if filters.get("status"):

		conditions["status"] = filters.status

	if filters.get("location_1"):

		conditions["location_1"] = filters.location_1



	locations = frappe.get_all(

		"Organization Unit",

		filters=conditions,

		fields=[

			"name as unit_name",

			"unit_code",

			"location_1",

			"organization_level",

			"status",

			"parent_organization_unit",

			"region",

			"city",

		],

		order_by="lft asc",

	)



	for location in locations:

		location["indent"] = max(cint(location.organization_level) - 1, 0)



	return locations

