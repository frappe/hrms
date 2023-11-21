// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Journal Entry", {
	refresh(frm) {
		frm.set_query("reference_name", "accounts", function(frm, cdt, cdn) {
			let jvd = frappe.get_doc(cdt, cdn);

			// filters for hrms doctypes
			if (jvd.reference_type === "Expense Claim") {
				return {
					filters: {
						"total_sanctioned_amount": [">", 0],
						"status": ["!=", "Paid"],
						"docstatus": 1
					}
				};
			}

			if (jvd.reference_type === "Employee Advance") {
				return {
					filters: {
						"docstatus": 1
					}
				};
			}

			if (jvd.reference_type === "Payroll Entry") {
				return {
					query: "hrms.payroll.doctype.payroll_entry.payroll_entry.get_payroll_entries_for_jv",
				};
			}

			// filters for erpnext doctypes
			if (jvd.reference_type === "Journal Entry") {
				frappe.model.validate_missing(jvd, "account");
				return {
					query: "erpnext.accounts.doctype.journal_entry.journal_entry.get_against_jv",
					filters: {
						account: jvd.account,
						party: jvd.party
					}
				};
			}

			const out = {
				filters: [
					[jvd.reference_type, "docstatus", "=", 1]
				]
			};

			if (in_list(["Sales Invoice", "Purchase Invoice"], jvd.reference_type)) {
				out.filters.push([jvd.reference_type, "outstanding_amount", "!=", 0]);
				// Filter by cost center
				if (jvd.cost_center) {
					out.filters.push([jvd.reference_type, "cost_center", "in", ["", jvd.cost_center]]);
				}
				// account filter
				frappe.model.validate_missing(jvd, "account");
				const party_account_field = jvd.reference_type === "Sales Invoice" ? "debit_to": "credit_to";
				out.filters.push([jvd.reference_type, party_account_field, "=", jvd.account]);
			}

			if (in_list(["Sales Order", "Purchase Order"], jvd.reference_type)) {
				// party_type and party mandatory
				frappe.model.validate_missing(jvd, "party_type");
				frappe.model.validate_missing(jvd, "party");

				out.filters.push([jvd.reference_type, "per_billed", "<", 100]);
			}

			if (jvd.party_type && jvd.party) {
				let party_field = "";
				if (jvd.reference_type.indexOf("Sales") === 0) {
					party_field = "customer";
				} else if (jvd.reference_type.indexOf("Purchase") === 0) {
					party_field = "supplier";
				}

				if (party_field) {
					out.filters.push([jvd.reference_type, party_field, "=", jvd.party]);
				}
			}

			return out;
		});
	}
})