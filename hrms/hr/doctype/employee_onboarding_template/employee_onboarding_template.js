// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Onboarding Template", {
	setup: function (frm) {
		frm.set_query("department", function () {
			return {
				filters: {
					company: frm.doc.company,
				},
			};
		});
	},

	onload: function (frm) {
		if (!frm.is_new() || frm.doc.activities?.length) return;

		frappe
			.xcall(
				"hrms.hr.doctype.employee_onboarding_template.employee_onboarding_template.get_standard_activities",
			)
			.then((activities) => {
				activities.forEach((activity) => frm.add_child("activities", activity));
				frm.refresh_field("activities");
			});
	},
});
