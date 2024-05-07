// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.require("assets/hrms/js/salary_slip_deductions_report_filters.js", function() {
	frappe.query_reports["Salary Payments Based On Payment Mode"] = hrms.salary_slip_deductions_report_filters;
});
