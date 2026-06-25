// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Vacant Positions"] = {
	filters: [
		{
			fieldname: "organization_unit",
			label: __("Organization Unit"),
			fieldtype: "Link",
			options: "Organization Unit",
		},
		{
			fieldname: "site_organization_unit",
			label: __("Site Organization Unit"),
			fieldtype: "Link",
			options: "Organization Unit",
		},
		{
			fieldname: "job_grade",
			label: __("Job Grade"),
			fieldtype: "Link",
			options: "Job Grade",
		},
		{
			fieldname: "position_status",
			label: __("Status"),
			fieldtype: "Select",
			options: ["", "Active", "Inactive"],
			default: "Active",
		},
	],
};
