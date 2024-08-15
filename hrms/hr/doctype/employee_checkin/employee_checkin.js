// Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Checkin", {
	refresh: async (frm) => {
		if (!frm.doc.__islocal) frm.trigger("add_fetch_shift_button");
	},

	add_fetch_shift_button(frm) {
		if (frm.doc.attendace) return;
		frm.add_custom_button(__("Fetch Shift"), function () {
			const previous_shift = frm.doc.shift;
			frappe.call({
				method: "fetch_shift",
				doc: frm.doc,
				freeze: true,
				freeze_message: __("Fetching Shift"),
				callback: function () {
					if (previous_shift === frm.doc.shift) return;
					frm.dirty();
					frm.save();
					frappe.show_alert({
						message: __("Shift has been successfully updated to {0}.", [
							frm.doc.shift,
						]),
						indicator: "green",
					});
				},
			});
		});
	},
});
