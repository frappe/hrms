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
				error: function (err) {
					reject(err);
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
	const expense_claim = expense_claims[0];
	const expense_claim_link = frappe.utils.get_form_link(
		"Expense Claim",
		expense_claim.name,
		true,
	);

	if (expense_claim.action === "delete") {
		return __(
			"Cancelling Vehicle Log {0} will delete draft Expense Claim {1} because it only contains Vehicle Expenses.<br><br>Do you want to continue?",
			[vehicle_log.bold(), expense_claim_link],
		);
	}

	return __(
		"Cancelling Vehicle Log {0} will update draft Expense Claim {1}.<br><br>Vehicle Expenses rows will be removed. Other expenses will remain.<br><br>Do you want to continue?",
		[vehicle_log.bold(), expense_claim_link],
	);
}
