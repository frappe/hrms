// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee", {
	setup: function (frm) {
		frm.set_query("leave_policy", function() {
			return {
				filters: {
					"docstatus": 1
				}
			};
		});

		frm.set_query("payroll_cost_center", function() {
			return {
				filters: {
					"company": frm.doc.company,
					"is_group": 0
				}
			};
		});
	}
})