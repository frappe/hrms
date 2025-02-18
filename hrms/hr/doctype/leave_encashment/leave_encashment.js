// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.provide("erpnext.accounts.dimensions");

frappe.ui.form.on("Leave Encashment", {
	onload: function (frm) {
		// Ignore cancellation of doctype on cancel all.
		frm.ignore_doctypes_on_cancel_all = ["Leave Ledger Entry"];
		erpnext.accounts.dimensions.setup_dimension_filters(frm, frm.doctype);
	},
	setup: function (frm) {
		frm.set_query("leave_type", function () {
			return {
				filters: {
					allow_encashment: 1,
				},
			};
		});
		frm.set_query("leave_period", function () {
			return {
				filters: {
					is_active: 1,
				},
			};
		});

		frm.set_query("payable_account", function () {
			if (!frm.doc.employee) {
				frappe.msgprint(__("Please select employee first"));
			}
			let company_currency = erpnext.get_currency(frm.doc.company);
			let currencies = [company_currency];
			if (frm.doc.currency && frm.doc.currency != company_currency) {
				currencies.push(frm.doc.currency);
			}

			return {
				filters: {
					company: frm.doc.company,
					account_currency: ["in", currencies],
				},
			};
		});
	},
	refresh: function (frm) {
		cur_frm.set_intro("");
		if (frm.doc.__islocal && !frappe.user_roles.includes("Employee")) {
			frm.set_intro(__("Fill the form and save it"));
		}

		if (
			frm.doc.docstatus === 1 &&
			frm.doc.pay_via_payment_entry == 1 &&
			frm.doc.status !== "Paid"
		) {
			frm.add_custom_button(
				__("Payment"),
				function () {
					frm.events.make_payment_entry(frm);
				},
				__("Create"),
			);
		}

		hrms.leave_utils.add_view_ledger_button(frm);
	},
	employee: function (frm) {
		if (frm.doc.employee) {
			frappe.run_serially([
				() => frm.trigger("get_employee_currency"),
				() => frm.trigger("get_leave_details_for_encashment"),
			]);
		}
	},
	company: function (frm) {
		erpnext.accounts.dimensions.update_dimension(frm, frm.doctype);
	},
	leave_type: function (frm) {
		frm.trigger("get_leave_details_for_encashment");
	},
	encashment_date: function (frm) {
		frm.trigger("get_leave_details_for_encashment");
	},
	get_leave_details_for_encashment: function (frm) {
		frm.set_value("actual_encashable_days", 0);
		frm.set_value("encashment_days", 0);

		if (frm.doc.docstatus === 0 && frm.doc.employee && frm.doc.leave_type) {
			return frappe.call({
				method: "get_leave_details_for_encashment",
				doc: frm.doc,
				callback: function (r) {
					frm.refresh_fields();
				},
			});
		}
	},

	get_employee_currency: function (frm) {
		frappe.call({
			method: "hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment.get_employee_currency",
			args: {
				employee: frm.doc.employee,
			},
			callback: function (r) {
				if (r.message) {
					frm.set_value("currency", r.message);
					frm.refresh_fields();
				}
			},
		});
	},
	make_payment_entry: function (frm) {
		return frappe.call({
			method: "hrms.overrides.employee_payment_entry.get_payment_entry_for_employee",
			args: {
				dt: frm.doc.doctype,
				dn: frm.doc.name,
			},
			callback: function (r) {
				var doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			},
		});
	},
});
