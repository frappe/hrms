// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("City", {
	setup(frm) {
		frm.set_query("region", () => ({
			filters: { status: "Active" },
		}));

		frm.set_query("zone", () => {
			const filters = { status: "Active" };
			if (frm.doc.region) filters.region = frm.doc.region;
			return { filters };
		});
	},

	region(frm) {
		if (frm.doc.zone) {
			frappe.db.get_value("Zone", frm.doc.zone, "region", (r) => {
				if (r && r.region !== frm.doc.region) frm.set_value("zone", null);
			});
		}
	},
});
