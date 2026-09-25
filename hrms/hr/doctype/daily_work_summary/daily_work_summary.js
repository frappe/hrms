// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Daily Work Summary", {
	refresh: function (frm) {
		frm.dashboard.set_headline_alert(
			__("Daily Work Summary is deprecated and will be removed in an upcoming release."),
			"orange",
		);
	},
});
