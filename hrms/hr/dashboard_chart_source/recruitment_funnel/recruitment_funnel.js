frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Recruitment Funnel"] = {
	method: "hrms.hr.dashboard_chart_source.recruitment_funnel.recruitment_funnel.get_data",
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
