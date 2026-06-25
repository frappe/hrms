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

			"fieldname": "unit_name",

			"fieldtype": "Link",

			"options": "Organization Unit",

			"width": 280,

		},

		{"label": _("Code"), "fieldname": "unit_code", "fieldtype": "Data", "width": 120},

		{

			"label": _("District"),

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

			"label": _("Zone"),

			"fieldname": "zone",

			"fieldtype": "Link",

			"options": "Zone",

			"width": 180,

		},

		{

			"label": _("City"),

			"fieldname": "city",

			"fieldtype": "Link",

			"options": "City",

			"width": 180,

		},

		{

			"label": _("Woreda"),

			"fieldname": "woreda",

			"fieldtype": "Link",

			"options": "Woreda",

			"width": 180,

		},

		{"label": _("Address Line 1"), "fieldname": "address_line_1", "fieldtype": "Data", "width": 220},

		{"label": _("Phone"), "fieldname": "phone", "fieldtype": "Data", "width": 140},

		{"label": _("Email"), "fieldname": "email", "fieldtype": "Data", "width": 180},

		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},

	]





def get_data(filters):

	conditions = {"location_1": "Branch"}

	if filters.get("status"):

		conditions["status"] = filters.status

	if filters.get("region"):

		conditions["region"] = filters.region

	if filters.get("zone"):

		conditions["zone"] = filters.zone

	if filters.get("city"):

		conditions["city"] = filters.city

	if filters.get("woreda"):

		conditions["woreda"] = filters.woreda

	if filters.get("district"):

		conditions["parent_organization_unit"] = filters.district



	return frappe.get_all(

		"Organization Unit",

		filters=conditions,

		fields=[

			"name as unit_name",

			"unit_code",

			"parent_organization_unit",

			"region",

			"zone",

			"city",

			"woreda",

			"address_line_1",

			"phone",

			"email",

			"status",

		],

		order_by="unit_name asc",

	)

