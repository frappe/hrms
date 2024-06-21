// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Leave Policy Assignment", {
	onload: function (frm) {
		frm.ignore_doctypes_on_cancel_all = ["Leave Ledger Entry"];

		frm.set_query("leave_policy", function () {
			return {
				filters: {
					docstatus: 1,
				},
			};
		});
		frm.set_query("leave_period", function () {
			return {
				filters: {
					is_active: 1,
					company: frm.doc.company,
				},
			};
		});
	},

	before_submit: async function (frm) {
		if (frm.doc.mid_period_change) {
			const promise = new Promise((resolve, reject) => {
				frappe.confirm(
					__(
						"Are you sure you want to apply the new leave policy <b style='color:red;'>in the middle of current policy assignment period</b>? This change will take effect immediately and cannot be undone.",
					),
					resolve,
					reject,
				);
			});
			await promise.catch(() => {
				$(".primary-action").prop("disabled", false);
				frappe.throw(__("Please untick <b>Allow Mid-Period Policy Change</b> checkbox."));
			});
		}
	},

	assignment_based_on: function (frm) {
		if (frm.doc.assignment_based_on) {
			frm.events.set_effective_date(frm);
		} else {
			frm.set_value("effective_from", "");
			frm.set_value("effective_to", "");
		}
	},

	leave_period: function (frm) {
		if (frm.doc.leave_period) {
			frm.events.set_effective_date(frm);
		}
	},

	set_effective_date: function (frm) {
		if (frm.doc.assignment_based_on == "Leave Period" && frm.doc.leave_period) {
			frappe.model.with_doc("Leave Period", frm.doc.leave_period, function () {
				let from_date = frappe.model.get_value(
					"Leave Period",
					frm.doc.leave_period,
					"from_date",
				);
				let to_date = frappe.model.get_value(
					"Leave Period",
					frm.doc.leave_period,
					"to_date",
				);
				frm.set_value("effective_from", from_date);
				frm.set_value("effective_to", to_date);
			});
		} else if (frm.doc.assignment_based_on == "Joining Date" && frm.doc.employee) {
			frappe.model.with_doc("Employee", frm.doc.employee, function () {
				let from_date = frappe.model.get_value(
					"Employee",
					frm.doc.employee,
					"date_of_joining",
				);
				frm.set_value("effective_from", from_date);
				frm.set_value(
					"effective_to",
					frappe.datetime.add_months(frm.doc.effective_from, 12),
				);
			});
		}
		frm.refresh();
	},
});
