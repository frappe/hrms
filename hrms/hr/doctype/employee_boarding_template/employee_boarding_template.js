// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Boarding Template", {
	setup: function (frm) {
		frm.set_query("department", function () {
			return {
				filters: {
					company: frm.doc.company,
				},
			};
		});
		frm.fields_dict.required_documents.grid.update_docfield_property(
			"attachment",
			"hidden",
			1,
		);
	},

	onload: function (frm) {
		if (!frm.is_new() || frm.doc.preboarding_activities?.length) return;

		frappe
			.xcall(
				"hrms.hr.doctype.employee_boarding_template.employee_boarding_template.get_standard_activities",
			)
			.then((activities) => {
				activities.forEach((activity) =>
					frm.add_child("preboarding_activities", activity),
				);
				frm.refresh_field("preboarding_activities");
			});
	},
});
