// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shift Schedule", {
	refresh(frm) {
		if (frm.doc.docstatus === 1)
			hrms.add_shift_tools_button_to_form(frm, {
				action: "Assign Shift Schedule",
				shift_schedule: frm.doc.name,
			});
	},
});
