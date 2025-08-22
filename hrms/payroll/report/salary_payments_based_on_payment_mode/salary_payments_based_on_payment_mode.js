// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Salary Payments Based On Payment Mode"] = $.extend(
	{},
	hrms.salary_slip_deductions_report_filters,
	{
		formatter: function (value, row, column, data, default_formatter) {
			value = default_formatter(value, row, column, data);
			if (data.branch && data.branch.includes("Total") && column.colIndex === 1) {
				value = value.bold();
			}
			return value;
		},
	},
);
