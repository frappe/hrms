// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Employee CTC Break-up"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			reqd: 1,
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
			reqd: 1,
			get_query: function () {
				let company = frappe.query_report.get_filter_value("company");
				return {
					filters: {
						company: company,
					},
				};
			},
			on_change: function () {
				frappe.query_report.set_filter_value("salary_structure_assignment", "");
			},
		},
		{
			fieldname: "salary_structure_assignment",
			label: __("Salary Structure Assignment"),
			fieldtype: "Link",
			options: "Salary Structure Assignment",
			reqd: 1,
			get_query: function () {
				let employee = frappe.query_report.get_filter_value("employee");
				if (!employee) return;
				return {
					filters: {
						employee: employee,
						docstatus: 1,
					},
				};
			},
		},
	],
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data?.bold && value) value = `<strong>${value}</strong>`;
		if (column.fieldname == "type" && value) {
			let indicator_color = value === "Fixed" ? "blue" : "orange";
			value = `<span class="indicator-pill no-indicator-dot ${indicator_color}">${value}</span>`;
		}
		return value;
	},
};
