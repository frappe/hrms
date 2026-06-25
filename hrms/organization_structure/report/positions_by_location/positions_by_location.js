// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Positions by Location"] = {
	filters: [
		{
			fieldname: "location_1",
			label: __("Location"),
			fieldtype: "Select",
			options: ["", "Head Office", "District Office", "Branch"],
		},
	],
};
