// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Salary Payments via ECS"] = $.extend(
	{},
	hrms.salary_slip_deductions_report_filters,
	{
		filters: [
			...hrms.salary_slip_deductions_report_filters.filters,
			{
				fieldname: "type",
				label: __("Type"),
				fieldtype: "Select",
				options: ["", "Bank", "Cash", "Cheque"],
			},
		],
	},
);
