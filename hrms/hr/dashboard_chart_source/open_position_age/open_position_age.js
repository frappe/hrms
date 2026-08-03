frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Open Position Age"] = {
	method: "hrms.hr.dashboard_chart_source.open_position_age.open_position_age.get_data",
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
