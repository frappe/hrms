// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors

// For license information, please see license.txt



frappe.query_reports["Branch List"] = {

	filters: [

		{

			fieldname: "status",

			label: __("Status"),

			fieldtype: "Select",

			options: ["", "Active", "Inactive"],

		},

		{

			fieldname: "region",

			label: __("Region"),

			fieldtype: "Link",

			options: "Region",

		},

		{

			fieldname: "zone",

			label: __("Zone"),

			fieldtype: "Link",

			options: "Zone",

		},

		{

			fieldname: "city",

			label: __("City"),

			fieldtype: "Link",

			options: "City",

		},

		{

			fieldname: "woreda",

			label: __("Woreda"),

			fieldtype: "Link",

			options: "Woreda",

		},

		{

			fieldname: "district",

			label: __("District"),

			fieldtype: "Link",

			options: "Organization Unit",

			get_query: () => ({

				filters: { location_1: "District Office" },

			}),

		},

	],

};

