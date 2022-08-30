// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Goal', {
	refresh: function(frm) {
		if (!frm.doc.__islocal) {
			if (frm.doc.status !== "Archived") {
				frm.add_custom_button(__("Archive"), function() {
					frm.set_value("status", "Archived");
					frm.save();
				});
			} else {
				frm.add_custom_button(__("Unarchive"), function() {
					frm.set_value("status", "");
					frm.save();
				});
			}
		}
	}
});
