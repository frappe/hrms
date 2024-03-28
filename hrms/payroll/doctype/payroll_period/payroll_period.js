// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Payroll Period", {
	refresh: function (frm) {
		// sets start date and end date as that of the current fiscal year if no payroll period exists
		frappe.db.exists("Payroll Period").then((period_exists) => {
			if (!period_exists) {
				frm.set_value(
					"start_date",
					frappe.defaults.get_default("year_start_date")
				);
				frm.set_value("end_date", frappe.defaults.get_default("year_end_date"));
			}
		});
	},
});
