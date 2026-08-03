frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Interviewer Load"] = {
	method: "hrms.hr.dashboard_chart_source.interviewer_load.interviewer_load.get_data",
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
	],
};
