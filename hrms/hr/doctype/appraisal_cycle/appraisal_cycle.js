// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Appraisal Cycle", {
	get_employees: function(frm) {
		frappe.call({
			method: "get_employees",
			doc: frm.doc,
			freeze: true,
			freeze_message: __("Fetching Employees"),
			callback: function() {
				refresh_field("appraisee_list");
			}
		});
	}
});
