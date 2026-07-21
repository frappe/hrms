// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Department", {
	refresh: function (frm) {
		frm.set_query("payroll_cost_center", function () {
			return {
				filters: {
					company: frm.doc.company,
					is_group: 0,
				},
			};
		});

		["leave_approvers", "expense_approvers", "shift_request_approver"].forEach((table) => {
			frm.set_query("approver", table, function () {
				return {
					filters: {
						user_type: "System User",
					},
				};
			});
		});
	},
});
