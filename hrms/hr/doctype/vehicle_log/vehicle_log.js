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
				method: "hrms.hr.doctype.vehicle_log.vehicle_log.get_draft_expense_claim_cancellation_actions",
				args: {
					vehicle_log: frm.doc.name,
				},
				callback: function (r) {
					const expense_claims = r.message || [];
					if (!expense_claims.length) {
						resolve();
						return;
					}

					frappe.confirm(
						get_expense_claim_cancellation_message(expense_claims, frm.doc.name),
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

function get_expense_claim_cancellation_message(expense_claims, vehicle_log) {
	const message_parts = [];
	const claims_to_delete = get_expense_claim_links(expense_claims, "delete");
	const claims_to_unlink = get_expense_claim_links(expense_claims, "unlink");

	if (claims_to_delete) {
		message_parts.push(__("Will be deleted: {0}", [claims_to_delete]));
	}

	if (claims_to_unlink) {
		message_parts.push(
			__("Will be unlinked, and Vehicle Expenses will be removed: {0}", [claims_to_unlink]),
		);
	}

	return __(
		"Cancelling Vehicle Log {0} will affect linked draft Expense Claims:<br><br>{1}<br><br>Do you want to proceed?",
		[vehicle_log.bold(), message_parts.join("<br>")],
	);
}

function get_expense_claim_links(expense_claims, action) {
	return expense_claims
		.filter((expense_claim) => expense_claim.action === action)
		.map((expense_claim) =>
			frappe.utils.get_form_link("Expense Claim", expense_claim.name, true),
		)
		.join(", ");
}
