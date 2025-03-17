// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

// import TestVue from "./test.vue";

frappe.ui.form.on("Provisional Plan", {
	refresh: function (frm) {
		$(".layout-side-section").remove();
		if (frm.doc.__islocal) {
			frm.$wrapper.find("[data-fieldname='details_tab']").hide();
			//hide primary button
			frm.page.clear_primary_action();
		} else {
			//sync
			if (!frm.doc.employees[0].shift) {
				frm.add_custom_button(__("Sync"), function () {
					frm.call("sync").then(() => {
						frm.reload_doc();
					});
				});
			}
		}

		let $wrapper = $(frm.fields_dict.roster_wrapper.wrapper).empty();

		frappe.require("roster.bundle.js").then(() => {
			console.log("roster.bundle.js loaded");
			frappe.roster = new frappe.ui.Roster({
				wrapper: $wrapper,
				frm: frm,
			});
		});
	},
	onload: function (frm) {
		// // console.log("onload");
		// frm.set_df_property("details_tab", "hidden", true);
		// frm.toggle_display("details_tab", false);
		// console.log("cniced");
	},
});
