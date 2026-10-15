// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Income Tax Computation"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			width: "90px",
			reqd: 1,
			on_change: (report) => {
				frappe.query_report.set_filter_value("employee", "");
				report.refresh();
			},
		},
		{
			fieldname: "payroll_period",
			label: __("Payroll Period"),
			fieldtype: "Link",
			options: "Payroll Period",
			width: "90px",
			reqd: 1,
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
			width: "90px",
			get_query: () => {
				return {
					filters: {
						company: frappe.query_report.get_filter_value("company"),
					},
				};
			},
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
			width: "90px",
		},

		{
			fieldname: "employee_status",
			label: __("Employee Status"),
			fieldtype: "Select",
			options: "Active\nInactive\nSuspended\nLeft",
			default: "Active",
			width: "90px",
		},
		{
			fieldname: "consider_tax_exemption_declaration",
			label: __("Consider Tax Exemption Declaration"),
			fieldtype: "Check",
			width: "180px",
		},
	],
};
