// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Advance", {
	setup: function (frm) {
		frm.set_query("employee", function () {
			return {
				filters: {
					status: "Active",
				},
			};
		});

		frm.set_query("advance_account", function () {
			if (!frm.doc.employee) {
				frappe.msgprint(__("Please select employee first"));
			}
			return {
				filters: {
					root_type: "Asset",
					is_group: 0,
					company: frm.doc.company,
					account_currency: frm.doc.currency,
					account_type: "Receivable",
				},
			};
		});
	},

	refresh: function (frm) {
		if (
			frm.doc.docstatus === 1 &&
			flt(frm.doc.paid_amount) < flt(frm.doc.advance_amount) &&
			frappe.model.can_create("Payment Entry") &&
			!(
				(frm.doc.repay_unclaimed_amount_from_salary == 1 && frm.doc.paid_amount) ||
				(frm.doc.__onload &&
					frm.doc.__onload.make_payment_via_journal_entry == 1 &&
					frm.doc.paid_amount)
			)
		) {
			frm.add_custom_button(
				__("Payment"),
				function () {
					frm.events.make_payment_entry(frm);
				},
				__("Create"),
			);
		} else if (
			frm.doc.docstatus === 1 &&
			flt(frm.doc.claimed_amount) < flt(frm.doc.paid_amount) - flt(frm.doc.return_amount) &&
			frappe.model.can_create("Expense Claim")
		) {
			frm.add_custom_button(
				__("Expense Claim"),
				function () {
					frm.events.make_expense_claim(frm);
				},
				__("Create"),
			);
		}
		frm.trigger("update_fields_label");

		if (
			frm.doc.docstatus === 1 &&
			flt(frm.doc.claimed_amount) < flt(frm.doc.paid_amount) - flt(frm.doc.return_amount)
		) {
			if (
				frm.doc.repay_unclaimed_amount_from_salary == 0 &&
				frappe.model.can_create("Journal Entry")
			) {
				frm.add_custom_button(
					__("Return"),
					function () {
						frm.trigger("make_return_entry");
					},
					__("Create"),
				);
			} else if (
				frm.doc.repay_unclaimed_amount_from_salary == 1 &&
				frappe.model.can_create("Additional Salary")
			) {
				frm.add_custom_button(
					__("Deduction from Salary"),
					function () {
						frm.events.make_deduction_via_additional_salary(frm);
					},
					__("Create"),
				);
			}
		}
	},

	make_deduction_via_additional_salary: function (frm) {
		frappe.call({
			method: "hrms.hr.doctype.employee_advance.employee_advance.create_return_through_additional_salary",
			args: {
				doc: frm.doc,
			},
			callback: function (r) {
				var doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			},
		});
	},

	make_payment_entry: function (frm) {
		let method = "hrms.overrides.employee_payment_entry.get_payment_entry_for_employee";
		if (frm.doc.__onload && frm.doc.__onload.make_payment_via_journal_entry) {
			method = "hrms.hr.doctype.employee_advance.employee_advance.make_bank_entry";
		}
		return frappe.call({
			method: method,
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

	make_expense_claim: function (frm) {
		return frappe.call({
			method: "hrms.hr.doctype.expense_claim.expense_claim.get_expense_claim",
			args: {
				advance_details: {
					employee_name: frm.doc.employee,
					company: frm.doc.company,
					currency: frm.doc.currency,
					employee_advance_name: frm.doc.name,
					posting_date: frm.doc.posting_date,
					paid_amount: frm.doc.paid_amount,
					base_paid_amount: frm.doc.base_paid_amount,
					claimed_amount: frm.doc.claimed_amount,
					return_amount: frm.doc.return_amount,
					payment_via_journal_entry: frm.doc.__onload.make_payment_via_journal_entry,
				},
			},
			callback: function (r) {
				const doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			},
		});
	},

	make_return_entry: function (frm) {
		frappe.call({
			method: "hrms.hr.doctype.employee_advance.employee_advance.make_return_entry",
			args: {
				employee: frm.doc.employee,
				company: frm.doc.company,
				employee_advance_name: frm.doc.name,
				return_amount: flt(frm.doc.paid_amount - frm.doc.claimed_amount),
				advance_account: frm.doc.advance_account,
				mode_of_payment: frm.doc.mode_of_payment,
				currency: frm.doc.currency,
			},
			callback: function (r) {
				const doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			},
		});
	},

	employee: function (frm) {
		if (frm.doc.employee) {
			frm.trigger("update_fields_label");
		}
	},

	update_fields_label: function (frm) {
		frm.set_currency_labels(["paid_amount"], frm.doc.currency);
		frm.set_currency_labels(["base_paid_amount"], erpnext.get_currency(frm.doc.company));
		frm.refresh_fields();
	},
});
