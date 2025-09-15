// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Full and Final Statement", {
	refresh: function (frm) {
		frm.events.set_queries(frm, "payables");
		frm.events.set_queries(frm, "receivables");

		if (frm.doc.docstatus == 1 && frm.doc.status == "Unpaid") {
			frm.add_custom_button(__("Create Journal Entry"), function () {
				frm.events.create_journal_entry(frm);
			});
		}
	},

	set_queries: function (frm, type) {
		frm.set_query("reference_document_type", type, function () {
			let modules = ["HR", "Payroll", "Loan Management"];
			return {
				filters: {
					istable: 0,
					issingle: 0,
					module: ["In", modules],
				},
			};
		});

		let filters = {};

		frm.set_query("reference_document", type, function (doc, cdt, cdn) {
			let fnf_doc = frappe.get_doc(cdt, cdn);

			frappe.model.with_doctype(fnf_doc.reference_document_type, function () {
				if (frappe.model.is_tree(fnf_doc.reference_document_type)) {
					filters["is_group"] = 0;
				}

				if (frappe.model.is_submittable(fnf_doc.reference_document_type)) {
					filters["docstatus"] = ["!=", 2];
				}

				if (frappe.meta.has_field(fnf_doc.reference_document_type, "company")) {
					filters["company"] = frm.doc.company;
				}

				if (frappe.meta.has_field(fnf_doc.reference_document_type, "employee")) {
					filters["employee"] = frm.doc.employee;
				}

				if (fnf_doc.reference_document_type === "Leave Encashment") {
					filters["status"] = "Unpaid";
					filters["pay_via_payment_entry"] = 1;
				}
			});

			return {
				filters: filters,
			};
		});
	},

	employee: function (frm) {
		frm.events.get_outstanding_statements(frm);
	},

	total_asset_recovery_cost: function (frm) {
		frm.trigger("calculate_total_receivable_amt");
	},

	get_outstanding_statements: function (frm) {
		if (frm.doc.employee) {
			frappe.call({
				method: "get_outstanding_statements",
				doc: frm.doc,
				callback: function () {
					frm.refresh();
				},
			});
		}
	},

	calculate_total_payable_amt: function (frm) {
		let total_payable_amount = 0;

		frm.doc.payables?.forEach(
			(row) => (total_payable_amount += flt(row.amount, precision("amount", row))),
		);
		frm.set_value(
			"total_payable_amount",
			flt(total_payable_amount, precision("total_payable_amount")),
		);
	},

	calculate_total_receivable_amt: function (frm) {
		let total_asset_recovery_cost = 0;
		let total_receivable_amount = 0;

		frm.doc.assets_allocated?.forEach((row) => {
			if (row.action === "Recover Cost") {
				total_asset_recovery_cost += flt(row.cost, precision("cost", row));
			}
		});

		frm.doc.receivables?.forEach(
			(row) => (total_receivable_amount += flt(row.amount, precision("amount", row))),
		);

		frm.set_value(
			"total_asset_recovery_cost",
			flt(total_asset_recovery_cost, precision("total_asset_recovery_cost")),
		);
		frm.set_value(
			"total_receivable_amount",
			flt(
				total_asset_recovery_cost + total_receivable_amount,
				precision("total_receivable_amount"),
			),
		);
	},

	create_journal_entry: function (frm) {
		frappe.call({
			method: "create_journal_entry",
			doc: frm.doc,
			callback: function (r) {
				var doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			},
		});
	},
});

frappe.ui.form.on("Full and Final Outstanding Statement", {
	reference_document: function (frm, cdt, cdn) {
		const child = locals[cdt][cdn];
		if (child.reference_document_type && child.reference_document) {
			frappe.call({
				method: "hrms.hr.doctype.full_and_final_statement.full_and_final_statement.get_account_and_amount",
				args: {
					ref_doctype: child.reference_document_type,
					ref_document: child.reference_document,
					company: frm.doc.company,
				},
				callback: function (r) {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, "account", r.message[0]);
						frappe.model.set_value(cdt, cdn, "amount", r.message[1]);
					}
				},
			});
		}
	},

	amount: function (frm, cdt, cdn) {
		const child_row = locals[cdt][cdn];
		const table = child_row.parentfield;

		if (table === "payables") {
			frm.trigger("calculate_total_payable_amt");
		} else {
			frm.trigger("calculate_total_receivable_amt");
		}
	},
});

frappe.ui.form.on("Full and Final Asset", {
	cost: function (frm, _cdt, _cdn) {
		frm.trigger("calculate_total_receivable_amt");
	},
});
