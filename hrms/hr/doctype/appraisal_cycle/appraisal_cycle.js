// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Appraisal Cycle", {
	refresh: function(frm) {
		frm.add_custom_button(__("Create Appraisals"), () => {
			frm.call("create_appraisals", {}, () => {
				frm.reload_doc();
			});
		}).addClass("btn-primary");
	},

	get_employees: function(frm) {
		frappe.call({
			method: "set_employees",
			doc: frm.doc,
			freeze: true,
			freeze_message: __("Fetching Employees"),
			callback: function() {
				refresh_field("appraisees");
			}
		});
	}
});
