// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Job Grade", {
	refresh(frm) {
		frm.add_custom_button(__("Positions"), () => {
			frappe.set_route("List", "Position", { job_grade: frm.doc.name });
		});
	},
});
