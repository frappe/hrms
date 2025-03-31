// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on("Attendance", {
	refresh(frm) {
		if (frm.doc.__islocal && !frm.doc.attendance_date) {
			frm.set_value("attendance_date", frappe.datetime.get_today());
		}

		frm.set_query("employee", () => {
			return {
				query: "erpnext.controllers.queries.employee_query",
			};
		}),
			(frm.fields_dict["leave_details"].grid.get_field("leave_application").get_query =
				function (doc) {
					return {
						filters: {
							company: doc.company,
							employee: doc.employee,
							from_date: ["<=", doc.attendance_date],
							to_date: [">=", doc.attendance_date],
						},
					};
				});
	},
});
