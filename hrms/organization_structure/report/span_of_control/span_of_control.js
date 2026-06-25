// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Span of Control"] = {
	filters: [
		{
			fieldname: "hide_leaf_positions",
			label: __("Only Positions with Reports"),
			fieldtype: "Check",
			default: 1,
		},
	],
};
