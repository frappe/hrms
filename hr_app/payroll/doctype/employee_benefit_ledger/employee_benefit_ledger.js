// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Benefit Ledger", {
	refresh: (frm) => {
		frm.set_read_only();
		frm.page.btn_primary.hide();
	},
});
