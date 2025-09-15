// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Leave Ledger"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.defaults.get_default("year_start_date"),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.defaults.get_default("year_end_date"),
		},
		{
			fieldname: "leave_type",
			label: __("Leave Type"),
			fieldtype: "Link",
			options: "Leave Type",
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
		},
		{
			fieldname: "status",
			label: __("Employee Status"),
			fieldtype: "Select",
			options: [
				"",
				{ value: "Active", label: __("Active") },
				{ value: "Inactive", label: __("Inactive") },
				{ value: "Suspended", label: __("Suspended") },
				{ value: "Left", label: __("Left", null, "Employee") },
			],
			default: "Active",
		},
		{
			label: __("Company"),
			fieldname: "company",
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
		},
		{
			fieldname: "transaction_type",
			label: __("Transaction Type"),
			fieldtype: "Select",
			options: [
				"",
				"Leave Allocation",
				"Leave Application",
				"Leave Encashment",
				"Leave Adjustment",
			],
		},
		{
			fieldname: "transaction_name",
			label: __("Transaction Name"),
			fieldtype: "Data",
		},
	],
	formatter: (value, row, column, data, default_formatter) => {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "leaves") {
			if (data?.leaves < 0) value = `<span style='color:red!important'>${value}</span>`;
			else value = `<span style='color:green!important'>${value}</span>`;
		}
		return value;
	},
	onload: () => {
		if (
			frappe.query_report.get_filter_value("from_date") &&
			frappe.query_report.get_filter_value("to_date")
		)
			return;

		const today = frappe.datetime.now_date();

		frappe.call({
			type: "GET",
			method: "hrms.hr.utils.get_leave_period",
			args: {
				from_date: today,
				to_date: today,
				company: frappe.defaults.get_user_default("Company"),
			},
			freeze: true,
			callback: (data) => {
				frappe.query_report.set_filter_value("from_date", data.message[0].from_date);
				frappe.query_report.set_filter_value("to_date", data.message[0].to_date);
			},
		});
	},
};
