// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Performance Feedback", {
	onload(frm) {
		frm.trigger("set_reviewer");
	},

	refresh(frm) {
		frm.trigger("set_filters");
	},

	employee(frm) {
		frm.set_value("appraisal", "");
	},

	appraisal(frm) {
		if (frm.doc.employee) {
			frm.call("set_feedback_criteria", () => {
				frm.refresh_field("feedback_ratings");
			});
		}
	},

	set_filters(frm) {
		frm.set_query("appraisal", () => {
			return {
				filters: {
					employee: frm.doc.employee,
				}
			}
		});

		frm.set_query("reviewer", () => {
			return {
				filters: {
					employee: ["!=", frm.doc.employee],
				}
			}
		});
	},

	set_reviewer(frm) {
		if (!frm.doc.reviewer) {
			frappe.db.get_value("Employee", { user_id: frappe.session.user }, "name").then(employee_record => {
				const session_employee = employee_record?.message?.name;
				if (session_employee)
					frm.set_value("reviewer", session_employee);
			});
		}
	}
});
