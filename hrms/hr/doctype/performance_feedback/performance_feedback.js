// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Performance Feedback", {
	refresh: function(frm) {
		frm.set_query("appraisal", () => {
			return {
				filters: {
					employee: frm.doc.employee,
				}
			}
		});
	},

	appraisal: function(frm) {
		if (frm.doc.employee) {
			frm.call("set_kras", () => {
				frm.refresh_field("kra_rating");
			});
		}
	},
});
