// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Organization Hierarchy"] = {
	filters: [
		{
			fieldname: "unit_type",
			label: __("Unit Type"),
			fieldtype: "Select",
			options: [
				"",
				"Executive",
				"Function",
				"Process",
				"Sub-Process",
				"Department",
				"District",
				"Team",
				"Branch",
				"Sub-Team",
				"Other",
			],
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: ["", "Active", "Inactive"],
		},
	],
	tree: true,
	name_field: "organization_unit",
	parent_field: "parent_organization_unit",
	initial_depth: 3,
};
