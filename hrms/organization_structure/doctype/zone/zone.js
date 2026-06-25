// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Zone", {
	setup(frm) {
		frm.set_query("region", () => ({
			filters: { status: "Active" },
		}));
	},
});
