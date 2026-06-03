// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
frappe.ui.form.on("Attendance Request", {
	refresh(frm) {
		frm.trigger("show_attendance_warnings");
	},

	show_attendance_warnings(frm) {
		if (!frm.is_new() && frm.doc.docstatus === 0) {
			frm.dashboard.clear_headline();

			frm.call("get_attendance_warnings").then((r) => {
				if (r.message?.length) {
					frm.dashboard.reset();
					frm.dashboard.add_section(
						frappe.render_template("attendance_warnings", {
							warnings: r.message || [],
						}),
						__("Attendance Warnings"),
					);
					frm.dashboard.show();
				}
			});
		}
	},

	employee(frm) {
		if (frm.doc.employee && frm.doc.from_date && !frm.doc.shift) {
			frm.trigger("set_employee_shift");
		}
	},

	from_date(frm) {
		if (frm.doc.employee && frm.doc.from_date && !frm.doc.shift) {
			frm.trigger("set_employee_shift");
		}
	},

	set_employee_shift(frm) {
		if (!frm.doc.employee || !frm.doc.from_date) return;

		frappe.call({
			method: "hrms.hr.doctype.attendance.attendance.get_employee_shift",
			args: {
				employee: frm.doc.employee,
				for_date: frm.doc.from_date,
				consider_default_shift: true,
			},
			callback(r) {
				if (r.message && !frm.doc.shift) {
					frm.set_value("shift", r.message);
				}
			},
		});
	},
});
