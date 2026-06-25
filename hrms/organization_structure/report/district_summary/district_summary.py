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

			"label": _("District"),

			"fieldname": "district",

			"fieldtype": "Link",

			"options": "Organization Unit",

			"width": 280,

		},

		{"label": _("Code"), "fieldname": "unit_code", "fieldtype": "Data", "width": 120},

		{"label": _("Total Branches"), "fieldname": "total_branches", "fieldtype": "Int", "width": 130},

		{"label": _("Active Branches"), "fieldname": "active_branches", "fieldtype": "Int", "width": 130},

		{"label": _("Inactive Branches"), "fieldname": "inactive_branches", "fieldtype": "Int", "width": 140},

		{

			"label": _("Region"),

			"fieldname": "region",

			"fieldtype": "Link",

			"options": "Region",

			"width": 180,

		},

		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},

	]





def get_data(filters):

	branch_counts = _get_branch_counts_by_parent()



	districts = frappe.get_all(

		"Organization Unit",

		filters={"location_1": "District Office"},

		fields=["name", "unit_code", "region", "status"],

		order_by="name asc",

	)



	data = []

	for district in districts:

		counts = branch_counts.get(

			district.name, {"total_branches": 0, "active_branches": 0, "inactive_branches": 0}

		)

		data.append(

			{

				"district": district.name,

				"unit_code": district.unit_code,

				"region": district.region,

				"status": district.status,

				**counts,

			}

		)



	return data





def _get_branch_counts_by_parent():

	counts = {}

	for branch in frappe.get_all(

		"Organization Unit",

		filters={"location_1": "Branch", "parent_organization_unit": ["is", "set"]},

		fields=["parent_organization_unit", "status"],

	):

		row = counts.setdefault(

			branch.parent_organization_unit,

			{"total_branches": 0, "active_branches": 0, "inactive_branches": 0},

		)

		row["total_branches"] += 1

		if branch.status == "Active":

			row["active_branches"] += 1

		elif branch.status == "Inactive":

			row["inactive_branches"] += 1



	return counts

