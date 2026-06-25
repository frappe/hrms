// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors

// For license information, please see license.txt



frappe.query_reports["Location Hierarchy"] = {

	filters: [

		{

			fieldname: "location_1",

			label: __("Location"),

			fieldtype: "Select",

			options: ["", "Head Office", "District Office", "Branch"],

		},

		{

			fieldname: "status",

			label: __("Status"),

			fieldtype: "Select",

			options: ["", "Active", "Inactive"],

		},

	],

	tree: true,

	name_field: "unit_name",

	parent_field: "parent_organization_unit",

	initial_depth: 3,

};

