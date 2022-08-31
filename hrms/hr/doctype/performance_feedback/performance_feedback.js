// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Performance Feedback', {
	// refresh: function(frm) {

	// },
	employee: function(frm) {
		if (frm.doc.employee) {
			frappe.call({
				"method": "hrms.hr.doctype.performance_feedback.performance_feedback.get_kra",
				args: {
					employee: frm.doc.employee
				},
				callback: function(data) {
					frm.doc.kra_rating = [];
					$.each(data.message.goals, function(_i, e) {
						let entry = frm.add_child("kra_rating");
						entry.kra = e.kra;
						entry.per_weightage = e.per_weightage;
					});
					refresh_field("kra_rating");
				}
			});
		}
	},
});
