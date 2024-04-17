// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Shift Attendance"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.month_start(),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.month_end(),
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
		},
		{
			fieldname: "shift",
			label: __("Shift Type"),
			fieldtype: "Link",
			options: "Shift Type",
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			reqd: 1,
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "late_entry",
			label: __("Late Entry"),
			fieldtype: "Check",
		},
		{
			fieldname: "early_exit",
			label: __("Early Exit"),
			fieldtype: "Check",
		},
		{
			fieldname: "consider_grace_period",
			label: __("Consider Grace Period"),
			fieldtype: "Check",
			default: 1,
		},
	],
	formatter: (value, row, column, data, default_formatter) => {
		value = default_formatter(value, row, column, data);
		if (
			(column.fieldname === "in_time" && data.late_entry) ||
			(column.fieldname === "out_time" && data.early_exit)
		) {
			value = `<span style='color:red!important'>${value}</span>`;
		}
		return value;
	},
};
