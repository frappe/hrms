// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Woreda", {
	setup(frm) {
		frm.set_query("city", () => ({
			filters: { status: "Active" },
		}));
	},
});
