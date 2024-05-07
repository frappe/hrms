// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Payroll Period", {
<<<<<<< HEAD
<<<<<<< HEAD
	refresh: function (frm) {},
=======
	refresh: function (frm) {
		// sets start date and end date as that of the current fiscal year if no payroll period exists
		frappe.db.exists("Payroll Period").then((period_exists) => {
			if (!period_exists) {
				frm.set_value("start_date", frappe.defaults.get_default("year_start_date"));
				frm.set_value("end_date", frappe.defaults.get_default("year_end_date"));
			}
		});
=======
	onload: function (frm) {
		frm.trigger("set_start_date");
	},

	set_start_date: function (frm) {
		if (!frm.doc.__islocal) return;

		frappe.db
			.get_list("Payroll Period", {
				fields: ["end_date"],
				order_by: "end_date desc",
				limit: 1,
			})
			.then((result) => {
				// set start date based on end date of the last payroll period if found
				// else set it based on the current fiscal year's start date
				if (result.length) {
					const last_end_date = result[0].end_date;
					frm.set_value("start_date", frappe.datetime.add_days(last_end_date, 1));
				} else {
					frm.set_value("start_date", frappe.defaults.get_default("year_start_date"));
				}
			});
	},

	start_date: function (frm) {
		frm.set_value(
			"end_date",
			frappe.datetime.add_days(frappe.datetime.add_months(frm.doc.start_date, 12), -1),
		);
>>>>>>> 22a9000b3 (fix: set payroll period dates based on last payroll period/current fiscal year)
	},
>>>>>>> a3060da3d (feat(Create Payroll Period): set Start & End Date as that of Fiscal Year if no Payroll Period exists)
});
