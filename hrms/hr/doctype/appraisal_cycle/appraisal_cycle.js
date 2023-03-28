// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Appraisal Cycle", {
	refresh: function(frm) {
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__("View Goals"), () => {
				frappe.route_options = {
					company: frm.doc.company,
					appraisal_cycle: frm.doc.name,
				};
				frappe.set_route("Tree", "Goal");
			});

			if (frm.doc.status == "Completed") return;

			frm.add_custom_button(__("Create Appraisals"), () => {
				frm.call({
					method: "create_appraisals",
					doc: frm.doc,
					freeze: true,
				}).then((r) => {
					if (!r.exc) {
						frm.reload_doc();
					}
				});

			}).addClass("btn-primary");
		}
	},

	get_employees: function(frm) {
		frappe.call({
			method: "set_employees",
			doc: frm.doc,
			freeze: true,
			freeze_message: __("Fetching Employees"),
			callback: function() {
				refresh_field("appraisees");
				frm.dirty();
			}
		});
	}
});
