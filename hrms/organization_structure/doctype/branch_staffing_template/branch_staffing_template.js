// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Branch Staffing Template", {
	refresh(frm) {
		if (frm.is_new()) return;

		const total = (frm.doc.staffing_details || []).reduce(
			(sum, row) => sum + (row.quantity || 0),
			0,
		);
		frm.dashboard.set_headline(
			__("This plan provisions {0} position(s) per branch.", [total]),
		);

		frm.add_custom_button(__("Branches Using This Plan"), () => {
			frappe.set_route("Tree", "Organization Unit");
		});
	},
});
