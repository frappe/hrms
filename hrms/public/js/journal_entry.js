// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Journal Entry", {
	setup(frm) {
		frm.set_query("reference_name", "accounts", function(frm, cdt, cdn) {
			let jvd = frappe.get_doc(cdt, cdn);

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
		})
	}
})