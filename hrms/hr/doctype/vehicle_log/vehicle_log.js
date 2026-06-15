// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Vehicle Log", {
	setup: function (frm) {
		frm.set_query("employee", function () {
			return {
				filters: {
					status: "Active",
				},
			};
		});
	},
	refresh: function (frm) {
		if (frm.doc.docstatus == 1) {
			frm.add_custom_button(
				__("Expense Claim"),
				function () {
					frm.events.expense_claim(frm);
				},
				__("Create"),
			);
			frm.page.set_inner_btn_group_as_primary(__("Create"));
		}
	},

	before_cancel: function (frm) {
		return new Promise((resolve, reject) => {
			frappe.call({
				method: "hrms.hr.doctype.vehicle_log.vehicle_log.get_draft_expense_claims",
				args: {
					vehicle_log: frm.doc.name,
				},
				callback: function (r) {
					const expense_claims = r.message || [];
					if (!expense_claims.length) {
						resolve();
						return;
					}

					const expense_claim_links = expense_claims
						.map((name) => frappe.utils.get_form_link("Expense Claim", name, true))
						.join(", ");

					frappe.confirm(
						__(
							"Draft Expense Claim {0} will be unlinked once Vehicle Log {1} is cancelled. Do you want to proceed?",
							[expense_claim_links, frm.doc.name.bold()],
						),
						() => resolve(),
						() => reject(),
						__("Yes"),
						__("No"),
					);
				},
			});
		});
	},

	expense_claim: function (frm) {
		frappe.call({
			method: "hrms.hr.doctype.vehicle_log.vehicle_log.make_expense_claim",
			args: {
				docname: frm.doc.name,
			},
			callback: function (r) {
				var doc = frappe.model.sync(r.message);
				frappe.set_route("Form", "Expense Claim", r.message.name);
			},
		});
	},
});
