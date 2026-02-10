// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Training Feedback", {
	onload: function (frm) {
		frm.set_query("employee", function () {
			if (!frm.doc.training_event) {
				return {
					filters: {
						name: ["in", []],
					},
				};
			}

			return {
				query: "hrms.hr.doctype.training_feedback.training_feedback.get_training_event_employees",
				filters: {
					training_event: frm.doc.training_event,
				},
			};
		});
	},

	refresh: function (frm) {
		frm.trigger("toggle_employee_field");
	},

	training_event: function (frm) {
		frm.set_value("employee", "");
		frm.trigger("toggle_employee_field");
	},

	toggle_employee_field: function (frm) {
		frm.set_df_property("employee", "read_only", !frm.doc.training_event);
	},


});
