// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Delivery Trip", {
	refresh: function (frm) {
		if (frm.doc.docstatus === 1 && frm.doc.employee) {
			frm.add_custom_button(
				__("Expense Claim"),
				function () {
					frappe.model.open_mapped_doc({
						method: "hrms.hr.doctype.expense_claim.expense_claim.make_expense_claim_for_delivery_trip",
						frm: frm,
					});
				},
				__("Create"),
			);
		}
	},
});
