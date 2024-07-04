// Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Checkin", {
	refresh: async (frm) => {
		if (!frm.doc.__islocal) frm.trigger("add_fetch_shift_button");

		const allow_geolocation_tracking = await frappe.db.get_single_value(
			"HR Settings",
			"allow_geolocation_tracking",
		);

		if (!allow_geolocation_tracking) {
			hide_field(["fetch_geolocation", "latitude", "longitude", "geolocation"]);
			return;
		}
	},

	fetch_geolocation: (frm) => {
		hrms.fetch_geolocation(frm);
	},
});
