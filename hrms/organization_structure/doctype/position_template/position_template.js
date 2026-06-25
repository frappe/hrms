// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Position Template", {
	refresh(frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(__("Positions"), () => {
			frappe.set_route("List", "Position", { position_template: frm.doc.name });
		});
	},

	template_name(frm) {
		// suggest a template code from the initials of the name when left blank
		if (frm.doc.template_code || !frm.doc.template_name) return;

		const code = frm.doc.template_name
			.split(/\s+/)
			.map((word) => word[0])
			.join("")
			.toUpperCase()
			.slice(0, 4);
		frm.set_value("template_code", code);
	},
});
