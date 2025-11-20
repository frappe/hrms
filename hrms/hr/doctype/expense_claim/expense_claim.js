// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide("hrms.hr");
frappe.provide("erpnext.accounts.dimensions");

frappe.ui.form.on("Expense Claim", {
	setup: function (frm) {
		frm.set_query("employee_advance", "advances", function () {
			return {
				filters: [
					["docstatus", "=", 1],
					["employee", "=", frm.doc.employee],
					["paid_amount", ">", 0],
					["status", "not in", ["Claimed", "Returned", "Partly Claimed and Returned"]],
				],
			};
		});

		frm.set_query("expense_approver", function () {
			return {
				query: "hrms.hr.doctype.department_approver.department_approver.get_approvers",
				filters: {
					employee: frm.doc.employee,
					doctype: frm.doc.doctype,
				},
			};
		});

		frm.set_query("account_head", "taxes", function () {
			return {
				filters: [
					["company", "=", frm.doc.company],
					[
						"account_type",
						"in",
						["Tax", "Chargeable", "Income Account", "Expenses Included In Valuation"],
					],
				],
			};
		});

		frm.set_query("payable_account", function () {
			return {
				filters: {
					report_type: "Balance Sheet",
					account_type: "Payable",
					company: frm.doc.company,
					account_currency: frm.doc.currency,
					is_group: 0,
				},
			};
		});

		frm.set_query("task", function () {
			return {
				filters: {
					project: frm.doc.project,
				},
			};
		});

		frm.set_query("employee", function () {
			return {
				query: "erpnext.controllers.queries.employee_query",
			};
		});

		frm.set_query("department", function () {
			return {
				filters: {
					company: frm.doc.company,
				},
			};
		});
	},

	onload: function (frm) {
		erpnext.accounts.dimensions.setup_dimension_filters(frm, frm.doctype);

		if (frm.doc.docstatus == 0) {
			return frappe.call({
				method: "hrms.hr.doctype.leave_application.leave_application.get_mandatory_approval",
				args: {
					doctype: frm.doc.doctype,
				},
				callback: function (r) {
					if (!r.exc && r.message) {
						frm.toggle_reqd("expense_approver", true);
					}
				},
			});
		}

		frm.trigger("update_fields_label");
		frm.trigger("update_child_fields_label");
	},

	refresh: function (frm) {
		frm.trigger("toggle_fields");
		frm.trigger("add_ledger_buttons");

		if (
			frm.doc.docstatus === 1 &&
			frm.doc.status !== "Paid" &&
			frappe.model.can_create("Payment Entry")
		) {
			frm.add_custom_button(
				__("Payment"),
				function () {
					frm.events.make_payment_entry(frm);
				},
				__("Create"),
			);
		}
		frm.trigger("set_form_buttons");
		frm.trigger("update_fields_label");
		frm.trigger("update_child_fields_label");
		if (frm.is_new()) {
			frm.trigger("set_exchange_rate");
		}

		if (frm.doc.advances && frm.doc.total_exchange_gain_loss != 0) {
			frm.add_custom_button(
				__("View Exchange Gain/Loss Journals"),
				function () {
					frappe.set_route("List", "Journal Entry", {
						voucher_type: "Exchange Gain Or Loss",
						reference_name: frm.doc.name,
					});
				},
				__("View"),
			);
		}
	},

	validate: function (frm) {
		frm.trigger("calculate_total");
		frm.events.set_child_cost_center(frm);
	},

	currency: function (frm) {
		frm.trigger("update_fields_label");
		frm.trigger("update_child_fields_label");
		frm.trigger("set_exchange_rate");
	},

	set_exchange_rate: function (frm) {
		if (frm.doc.currency) {
			var from_currency = frm.doc.currency;
			var company_currency;
			if (!frm.doc.company) {
				company_currency = erpnext.get_currency(frappe.defaults.get_default("Company"));
			} else {
				company_currency = erpnext.get_currency(frm.doc.company);
			}
			if (from_currency != company_currency) {
				frappe.call({
					method: "erpnext.setup.utils.get_exchange_rate",
					args: {
						from_currency: from_currency,
						to_currency: company_currency,
					},
					callback: function (r) {
						frm.set_value("exchange_rate", flt(r.message));
						frm.set_df_property("exchange_rate", "hidden", 0);
						frm.set_df_property(
							"exchange_rate",
							"description",
							"1 " + frm.doc.currency + " = [?] " + company_currency,
						);
					},
				});
			} else {
				frm.set_value("exchange_rate", 1.0);
				frm.set_df_property("exchange_rate", "hidden", 1);
				frm.set_df_property("exchange_rate", "description", "");
			}
			frm.refresh_fields();
		}
	},

	update_fields_label: function (frm) {
		var company_currency = erpnext.get_currency(frm.doc.company);
		frm.set_currency_labels(
			[
				"base_total_sanctioned_amount",
				"base_total_taxes_and_charges",
				"base_total_advance_amount",
				"base_grand_total",
				"base_total_claimed_amount",
			],
			company_currency,
		);

		frm.set_currency_labels(
			[
				"total_sanctioned_amount",
				"total_taxes_and_charges",
				"total_advance_amount",
				"grand_total",
				"total_claimed_amount",
			],
			frm.doc.currency,
		);

		// toggle fields
		frm.toggle_display(
			[
				"base_total_sanctioned_amount",
				"base_total_advance_amount",
				"base_grand_total",
				"base_total_claimed_amount",
				"base_total_taxes_and_charges",
			],
			frm.doc.currency != company_currency,
		);
	},

	update_child_fields_label: function (frm) {
		var from_currency = frm.doc.currency;
		var company_currency = erpnext.get_currency(frm.doc.company);
		// expenses table
		frm.set_currency_labels(["amount", "sanctioned_amount"], from_currency, "expenses");
		frm.set_currency_labels(
			["base_amount", "base_sanctioned_amount"],
			company_currency,
			"expenses",
		);

		// advances table
		frm.set_currency_labels(
			["advance_paid", "unclaimed_amount", "allocated_amount"],
			from_currency,
			"advances",
		);
		frm.set_currency_labels(
			["base_advance_paid", "base_unclaimed_amount", "base_allocated_amount"],
			company_currency,
			"advances",
		);

		// taxes table
		frm.set_currency_labels(["tax_amount", "total"], from_currency, "taxes");
		frm.set_currency_labels(["base_tax_amount", "base_total"], company_currency, "taxes");
	},

	add_ledger_buttons: function (frm) {
		if (frm.doc.docstatus > 0 && frm.doc.approval_status !== "Rejected") {
			frm.add_custom_button(
				__("Accounting Ledger"),
				function () {
					frappe.route_options = {
						voucher_no: frm.doc.name,
						company: frm.doc.company,
						from_date: frm.doc.posting_date,
						to_date: moment(frm.doc.modified).format("YYYY-MM-DD"),
						group_by: "",
						show_cancelled_entries: frm.doc.docstatus === 2,
					};
					frappe.set_route("query-report", "General Ledger");
				},
				__("View"),
			);
		}

		if (!frm.doc.__islocal && frm.doc.docstatus === 1) {
			let entry_doctype, entry_reference_doctype, entry_reference_name;
			if (frm.doc.__onload.make_payment_via_journal_entry) {
				entry_doctype = "Journal Entry";
				entry_reference_doctype = "Journal Entry Account.reference_type";
				entry_reference_name = "Journal Entry.reference_name";
			} else {
				entry_doctype = "Payment Entry";
				entry_reference_doctype = "Payment Entry Reference.reference_doctype";
				entry_reference_name = "Payment Entry Reference.reference_name";
			}

			if (
				cint(frm.doc.total_amount_reimbursed) > 0 &&
				frappe.model.can_read(entry_doctype)
			) {
				// nosemgrep: frappe-semgrep-rules.rules.frappe-cur-frm-usage
				frm.add_custom_button(
					__("Bank Entries"),
					function () {
						frappe.route_options = {
							party_type: "Employee",
							party: frm.doc.employee,
							company: frm.doc.company,
						};
						frappe.set_route("List", entry_doctype);
					},
					__("View"),
				);
			}
		}
	},

	calculate_total: function (frm) {
		let total_claimed_amount = 0;
		let total_sanctioned_amount = 0;

		frm.doc.expenses.forEach((row) => {
			total_claimed_amount += row.amount;
			total_sanctioned_amount += row.sanctioned_amount;
		});

		frm.set_value(
			"total_claimed_amount",
			flt(total_claimed_amount, precision("total_claimed_amount")),
		);
		frm.set_value(
			"total_sanctioned_amount",
			flt(total_sanctioned_amount, precision("total_sanctioned_amount")),
		);

		frm.doc.expenses.forEach((row) => {
			set_in_company_currency(frm, row, ["amount", "sanctioned_amount"]);
		});
		frm.doc.advances.forEach((row) => {
			set_in_company_currency(frm, row, ["allocated_amount"]);
			set_in_company_currency(frm, row, ["unclaimed_amount"], row.exchange_rate);
		});
	},

	calculate_grand_total: function (frm) {
		var grand_total =
			flt(frm.doc.total_sanctioned_amount) +
			flt(frm.doc.total_taxes_and_charges) -
			flt(frm.doc.total_advance_amount);
		frm.set_value("grand_total", grand_total);
		set_in_company_currency(frm, frm.doc, [
			"total_sanctioned_amount",
			"total_advance_amount",
			"grand_total",
			"total_claimed_amount",
			"total_taxes_and_charges",
		]);
		frm.refresh_fields();
	},

	grand_total: function (frm) {
		frm.trigger("update_employee_advance_claimed_amount");
	},

	update_employee_advance_claimed_amount: function (frm) {
		let amount_to_be_allocated = frm.doc.total_sanctioned_amount;
		$.each(frm.doc.advances || [], function (i, advance) {
			if (amount_to_be_allocated >= advance.unclaimed_amount - advance.return_amount) {
				advance.allocated_amount =
					frm.doc.advances[i].unclaimed_amount - frm.doc.advances[i].return_amount;
				amount_to_be_allocated -= advance.allocated_amount;
			} else {
				advance.allocated_amount = amount_to_be_allocated;
				amount_to_be_allocated = 0;
			}
			set_in_company_currency(frm, advance, ["allocated_amount"]);
			frm.refresh_field("advances");
		});
	},
	make_payment_entry: function (frm) {
		let method = "hrms.overrides.employee_payment_entry.get_payment_entry_for_employee";
		if (frm.doc.__onload && frm.doc.__onload.make_payment_via_journal_entry) {
			method = "hrms.hr.doctype.expense_claim.expense_claim.make_bank_entry";
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

	company: function (frm) {
		erpnext.accounts.dimensions.update_dimension(frm, frm.doctype);
		var expenses = frm.doc.expenses;
		for (var i = 0; i < expenses.length; i++) {
			var expense = expenses[i];
			if (!expense.expense_type) {
				continue;
			}
			frappe.call({
				method: "hrms.hr.doctype.expense_claim.expense_claim.get_expense_claim_account_and_cost_center",
				args: {
					expense_claim_type: expense.expense_type,
					company: frm.doc.company,
				},
				callback: function (r) {
					if (r.message) {
						expense.default_account = r.message.account;
						expense.cost_center = r.message.cost_center;
					}
				},
			});
		}
	},

	is_paid: function (frm) {
		frm.trigger("toggle_fields");
	},

	toggle_fields: function (frm) {
		frm.toggle_reqd("mode_of_payment", frm.doc.is_paid);
	},

	employee: function (frm) {
		frm.events.get_advances(frm);
	},

	cost_center: function (frm) {
		frm.events.set_child_cost_center(frm);
	},

	mode_of_payment: async function (frm) {
		if (frm.doc.mode_of_payment) {
			var mode_of_payment_type = (
				await frappe.db.get_value("Mode of Payment", frm.doc.mode_of_payment, "type")
			)?.message?.type;
			frm.set_query("bank_or_cash_account", function () {
				return {
					filters: [
						["account_type", "=", mode_of_payment_type],
						["company", "=", frm.doc.company],
						["is_group", "=", 0],
						["account_currency", "=", frm.doc.currency],
					],
				};
			});
		}
	},

	set_child_cost_center: function (frm) {
		(frm.doc.expenses || []).forEach(function (d) {
			if (!d.cost_center) {
				d.cost_center = frm.doc.cost_center;
			}
		});
	},

	get_taxes: function (frm) {
		if (!frm.doc.taxes.length) return;

		frappe.call({
			method: "calculate_taxes",
			doc: frm.doc,
			callback: () => {
				refresh_field("taxes");
				frm.trigger("update_employee_advance_claimed_amount");
			},
		});
	},

	get_advances: function (frm) {
		frappe.model.clear_table(frm.doc, "advances");
		if (frm.doc.employee) {
			return frappe.call({
				method: "hrms.hr.doctype.expense_claim.expense_claim.get_advances",
				args: {
					expense_claim: frm.doc,
				},
				callback: function (r, rt) {
					if (r.message) {
						$.each(r.message, function (i, d) {
							var row = frappe.model.add_child(
								frm.doc,
								"Expense Claim Advance",
								"advances",
							);
							row.employee_advance = d.employee_advance;
							row.posting_date = d.posting_date;
							row.advance_account = d.advance_account;
							row.advance_paid = d.advance_paid;
							row.unclaimed_amount = d.unclaimed_amount;
							row.return_amount = flt(d.return_amount);
							row.allocated_amount = d.allocated_amount;
							row.exchange_rate = d.exchange_rate;
							row.payment_entry = d.payment_entry;
							row.payment_entry_reference = d.payment_entry_reference;
						});
						refresh_field("advances");
					}
				},
			});
		}
	},
	set_form_buttons: async function (frm) {
		let self_approval_not_allowed = frm.doc.__onload
			? frm.doc.__onload.self_expense_approval_not_allowed
			: 0;
		let current_employee = await hrms.get_current_employee();
		if (
			frm.doc.docstatus === 0 &&
			!frm.is_dirty() &&
			!frappe.model.has_workflow(frm.doctype)
		) {
			if (self_approval_not_allowed && current_employee == frm.doc.employee) {
				frm.set_df_property("status", "read_only", 1);
				frm.trigger("show_save_button");
			}
		}
	},
	show_save_button: function (frm) {
		frm.page.set_primary_action("Save", () => {
			frm.save();
		});
		$(".form-message").prop("hidden", true);
	},
});

frappe.ui.form.on("Expense Claim Detail", {
	expense_type: function (frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		if (!frm.doc.company) {
			d.expense_type = "";
			frappe.msgprint(__("Please set the Company"));
			this.frm.refresh_fields();
			return;
		}

		if (!d.expense_type) {
			return;
		}
		return frappe.call({
			method: "hrms.hr.doctype.expense_claim.expense_claim.get_expense_claim_account_and_cost_center",
			args: {
				expense_claim_type: d.expense_type,
				company: frm.doc.company,
			},
			callback: function (r) {
				if (r.message) {
					d.default_account = r.message.account;
					d.cost_center = r.message.cost_center;
				}
			},
		});
	},

	amount: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "sanctioned_amount", child.amount);
		set_in_company_currency(frm, child, ["amount", "sanctioned_amount"]);
	},

	sanctioned_amount: function (frm, cdt, cdn) {
		frm.trigger("calculate_total");
		frm.trigger("get_taxes");
		frm.trigger("calculate_grand_total");
		set_in_company_currency(frm, locals[cdt][cdn], ["sanctioned_amount"]);
	},

	cost_center: function (frm, cdt, cdn) {
		erpnext.utils.copy_value_in_all_rows(frm.doc, cdt, cdn, "expenses", "cost_center");
	},
});

frappe.ui.form.on("Expense Claim Advance", {
	employee_advance: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (!frm.doc.employee) {
			frappe.msgprint(__("Select an employee to get the employee advance."));
			frm.doc.advances = [];
			refresh_field("advances");
		} else {
			return frappe.call({
				method: "hrms.hr.doctype.expense_claim.expense_claim.get_advances",
				args: {
					expense_claim: frm.doc,
					advance_id: child.employee_advance,
				},
				callback: function (r, rt) {
					if (r.message) {
						child.employee_advance = r.message[0].employee_advance;
						child.posting_date = r.message[0].posting_date;
						child.advance_account = r.message[0].advance_account;
						child.advance_paid = r.message[0].advance_paid;
						child.unclaimed_amount = r.message[0].unclaimed_amount;
						child.return_amount = flt(r.message[0].return_amount);
						child.allocated_amount = flt(r.message[0].allocated_amount);
						child.exchange_rate = r.message[0].exchange_rate;
						child.payment_entry = r.message[0].payment_entry;
						child.payment_entry_reference = r.message[0].payment_entry_reference;
						set_in_company_currency(
							frm,
							child,
							["advance_paid", "unclaimed_amount"],
							r.message[0].exchange_rate,
						);
						set_in_company_currency(frm, child, ["allocated_amount"]);
						refresh_field("advances");
					}
				},
			});
		}
		frm.trigger("calculate_grand_total");
	},
});

frappe.ui.form.on("Expense Taxes and Charges", {
	account_head: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.account_head && !child.description) {
			// set description from account head
			child.description = child.account_head.split(" - ").slice(0, -1).join(" - ");
			refresh_field("taxes");
		}
	},

	calculate_total_tax: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		child.total = flt(frm.doc.total_sanctioned_amount) + flt(child.tax_amount);
		frm.trigger("calculate_tax_amount", cdt, cdn);
	},

	calculate_tax_amount: function (frm) {
		frm.doc.total_taxes_and_charges = 0;
		(frm.doc.taxes || []).forEach(function (d) {
			frm.doc.total_taxes_and_charges += d.tax_amount;
			set_in_company_currency(frm, d, ["tax_amount", "total"]);
		});
		frm.trigger("calculate_grand_total");
	},

	rate: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (!child.amount) {
			child.tax_amount = flt(frm.doc.total_sanctioned_amount) * (flt(child.rate) / 100);
		}
		frm.trigger("calculate_total_tax", cdt, cdn);
	},

	tax_amount: function (frm, cdt, cdn) {
		frm.trigger("calculate_total_tax", cdt, cdn);
	},
});

async function set_in_company_currency(frm, doc, fields, exchange_rate = frm.doc.exchange_rate) {
	await $.each(fields, function (i, f) {
		doc["base_" + f] = flt(
			flt(doc[f], precision(f, doc)) * exchange_rate,
			precision("base_" + f, doc),
		);
	});
}
