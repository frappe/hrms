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
		});

		frm.trigger("set_max_attendance_date");

		if (frm.doc.docstatus === 1 && frm.doc.status === "Absent") {
			frm.add_custom_button(
				__("Attendance Request"),
				() => {
					frappe.new_doc("Attendance Request", {
						employee: frm.doc.employee,
						from_date: frm.doc.attendance_date,
						to_date: frm.doc.attendance_date,
					});
				},
				__("Create"),
			);
		}
	},

	employee(frm) {
		if (frm.doc.employee && frm.doc.attendance_date && !frm.doc.shift) {
			frm.trigger("set_employee_shift");
		}
	},

	attendance_date(frm) {
		if (frm.doc.employee && frm.doc.attendance_date && !frm.doc.shift) {
			frm.trigger("set_employee_shift");
		}
	},

	status(frm) {
		frm.trigger("set_max_attendance_date");
	},

	set_max_attendance_date(frm) {
		const datepicker = frm.fields_dict.attendance_date?.datepicker;
		if (!datepicker) return;

		// leaves and attendance requests can be applied for in advance
		const allow_future_date = frm.doc.status === "On Leave" || frm.doc.attendance_request;

		datepicker.update({
			maxDate: allow_future_date
				? ""
				: frappe.datetime.str_to_obj(frappe.datetime.get_today()),
		});
	},

	set_employee_shift(frm) {
		if (!frm.doc.employee || !frm.doc.attendance_date) return;

		frappe.call({
			method: "hrms.hr.doctype.attendance.attendance.get_employee_shift",
			args: {
				employee: frm.doc.employee,
				for_date: frm.doc.attendance_date || frappe.datetime.get_today(),
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
