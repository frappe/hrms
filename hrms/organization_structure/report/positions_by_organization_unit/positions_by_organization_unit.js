// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Positions by Organization Unit"] = {
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
	],
};
