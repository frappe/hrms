// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Overtime Slip", {
	employee(frm) {
		if (frm.doc.employee) {
			frm.events.set_frequency_and_dates(frm).then(() => {
				frm.events.get_emp_details_and_overtime_duration(frm);
			});
		}
	},
	from_date: function (frm) {
		if (frm.doc.employee && frm.doc.from_date) {
			frm.events.set_frequency_and_dates(frm).then(() => {
				frm.events.get_emp_details_and_overtime_duration(frm);
			});
		}
	},
	set_frequency_and_dates: function (frm) {
		if (frm.doc.employee) {
			return frappe.call({
				method: "get_frequency_and_dates",
				doc: frm.doc,
				callback: function () {
					frm.refresh();
				},
			});
		}
	},
	get_emp_details_and_overtime_duration: function (frm) {
		if (frm.doc.employee) {
			return frappe.call({
				method: "get_emp_and_overtime_details",
				doc: frm.doc,
				callback: function () {
					frm.refresh();
				},
			});
		}
	},
});
