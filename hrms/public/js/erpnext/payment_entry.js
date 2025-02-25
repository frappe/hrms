// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Payment Entry", {
	refresh: function (frm) {
		frm.set_query("reference_doctype", "references", function () {
			let doctypes = [];

			if (frm.doc.party_type == "Customer") {
				doctypes = ["Sales Order", "Sales Invoice", "Journal Entry", "Dunning"];
			} else if (frm.doc.party_type == "Supplier") {
				doctypes = ["Purchase Order", "Purchase Invoice", "Journal Entry"];
			} else if (frm.doc.party_type == "Employee") {
				doctypes = [
					"Expense Claim",
					"Employee Advance",
					"Leave Encashment",
					"Journal Entry",
				];
			} else {
				doctypes = ["Journal Entry"];
			}

			return {
				filters: { name: ["in", doctypes] },
			};
		});

		frm.set_query("reference_name", "references", function (doc, cdt, cdn) {
			const child = locals[cdt][cdn];
			const filters = { docstatus: 1, company: doc.company };
			const party_type_doctypes = [
				"Sales Invoice",
				"Sales Order",
				"Purchase Invoice",
				"Purchase Order",
				"Expense Claim",
				"Leave Encashment",
				"Dunning",
			];

			if (in_list(party_type_doctypes, child.reference_doctype)) {
				filters[doc.party_type.toLowerCase()] = doc.party;
			}

			if (child.reference_doctype == "Expense Claim") {
				filters["is_paid"] = 0;
			}

			if (
				child.reference_doctype == "Employee Advance" ||
				child.reference_doctype == "Leave Encashment"
			) {
				filters["status"] = "Unpaid";
			}

			return {
				filters: filters,
			};
		});
	},

	get_order_doctypes: function (frm) {
		return ["Sales Order", "Purchase Order", "Expense Claim"];
	},

	get_invoice_doctypes: function (frm) {
		return ["Sales Invoice", "Purchase Invoice", "Expense Claim"];
	},
});

frappe.ui.form.on("Payment Entry Reference", {
	reference_name: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		if (row.reference_name && row.reference_doctype) {
			return frappe.call({
				method: "hrms.overrides.employee_payment_entry.get_payment_reference_details",
				args: {
					reference_doctype: row.reference_doctype,
					reference_name: row.reference_name,
					party_account_currency:
						frm.doc.payment_type == "Receive"
							? frm.doc.paid_from_account_currency
							: frm.doc.paid_to_account_currency,
					party_type: frm.doc.party_type,
					party: frm.doc.party,
				},
				callback: function (r, rt) {
					if (r.message) {
						$.each(r.message, function (field, value) {
							frappe.model.set_value(cdt, cdn, field, value);
						});

						let allocated_amount =
							frm.doc.unallocated_amount > row.outstanding_amount
								? row.outstanding_amount
								: frm.doc.unallocated_amount;

						frappe.model.set_value(cdt, cdn, "allocated_amount", allocated_amount);
						frm.refresh_fields();
					}
				},
			});
		}
	},
});
