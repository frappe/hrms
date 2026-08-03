frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Source to Hire Conversion"] = {
	method: "hrms.hr.dashboard_chart_source.source_to_hire_conversion.source_to_hire_conversion.get_data",
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
