// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Branches by Woreda"] = {
	filters: [
		{
			fieldname: "city",
			label: __("City"),
			fieldtype: "Link",
			options: "City",
		},
	],
};
