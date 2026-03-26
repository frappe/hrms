// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Salary Component", {
	setup: function (frm) {
		frm.set_query("account", "accounts", function (doc, cdt, cdn) {
			var d = locals[cdt][cdn];
			return {
				filters: {
					is_group: 0,
					company: d.company,
				},
			};
		});
		frm.set_query("earning_component_group", function () {
			return {
				filters: {
					is_group: 1,
					is_flexible_benefit: 1,
				},
			};
		});
	},

	refresh: function (frm) {
		hrms.payroll_utils.set_autocompletions_for_condition_and_formula(frm);

		if (!frm.doc.__islocal) {
			frm.trigger("add_update_structure_button");
			frm.add_custom_button(
				__("Salary Structure"),
				() => {
					frm.trigger("create_salary_structure");
				},
				__("Create"),
			);
		}
	},

	do_not_include_in_total: function (frm) {
		if (!frm.doc.do_not_include_in_total) {
			frm.set_value("do_not_include_in_accounts", 0);
		}
	},

	arrear_component: function (frm) {
		if (frm.doc.arrear_component) {
			frm.set_value("depends_on_payment_days", 1);
		}
	},

	is_flexible_benefit: function (frm) {
		if (frm.doc.is_flexible_benefit) {
			set_value_for_condition_and_formula(frm);
			frm.set_value("formula", "");
			frm.set_value("amount", 0);
		} else {
			frm.set_value("payout_method", "");
		}
	},

	payout_method: (frm) => {
		if (frm.doc.is_flexible_benefit) {
			if (
				[
					"Accrue and payout at end of payroll period",
					"Accrue per cycle, pay only on claim",
				].includes(frm.doc.payout_method)
			) {
				frm.set_value("accrual_component", 1);
			} else {
				frm.set_value("accrual_component", 0);
			}
		}
	},

	type: function (frm) {
		if (frm.doc.type == "Earning") {
			frm.set_value("is_tax_applicable", 1);
			frm.set_value("variable_based_on_taxable_salary", 0);
		}
		if (frm.doc.type == "Deduction") {
			frm.set_value("is_tax_applicable", 0);
			frm.set_value("is_flexible_benefit", 0);
			frm.set_value("accrual_component", 0);
		}
	},

	variable_based_on_taxable_salary: function (frm) {
		if (frm.doc.variable_based_on_taxable_salary) {
			set_value_for_condition_and_formula(frm);
		}
		frm.set_value("arrear_component", 0);
	},

	add_update_structure_button: function (frm) {
		for (const df of ["Condition", "Formula"]) {
			frm.add_custom_button(
				__("Sync {0}", [__(df)]),
				function () {
					frappe
						.call({
							method: "get_structures_to_be_updated",
							doc: frm.doc,
						})
						.then((r) => {
							if (r.message.length)
								frm.events.update_salary_structures(frm, df, r.message);
							else
								frappe.msgprint({
									message: __(
										"Salary Component {0} is currently not used in any Salary Structure.",
										[frm.doc.name.bold()],
									),
									title: __("No Salary Structures"),
									indicator: "orange",
								});
						});
				},
				__("Update Salary Structures"),
			);
		}
	},

	update_salary_structures: function (frm, df, structures) {
		let msg = __("{0} will be updated for the following Salary Structures: {1}.", [
			__(df),
			frappe.utils.comma_and(
				structures.map((d) =>
					frappe.utils.get_form_link("Salary Structure", d, true).bold(),
				),
			),
		]);
		msg += "<br>";
		msg += __("Are you sure you want to proceed?");
		frappe.confirm(msg, () => {
			frappe
				.call({
					method: "update_salary_structures",
					doc: frm.doc,
					args: {
						structures: structures,
						field: df.toLowerCase(),
						value: frm.get_field(df.toLowerCase()).value || "",
					},
				})
				.then((r) => {
					if (!r.exc) {
						frappe.show_alert({
							message: __("Salary Structures updated successfully"),
							indicator: "green",
						});
					}
				});
		});
	},

	create_salary_structure: function (frm) {
		frappe.model.with_doctype("Salary Structure", () => {
			const salary_structure = frappe.model.get_new_doc("Salary Structure");
			const salary_detail = frappe.model.add_child(
				salary_structure,
				frm.doc.type === "Earning" ? "earnings" : "deductions",
			);
			salary_detail.salary_component = frm.doc.name;
			frappe.set_route("Form", "Salary Structure", salary_structure.name);
		});
	},
});

var set_value_for_condition_and_formula = function (frm) {
	frm.set_value({
		formula: null,
		condition: null,
		amount_based_on_formula: 0,
		statistical_component: 0,
		do_not_include_in_total: 0,
		do_not_include_in_accounts: 0,
		depends_on_payment_days: 0,
	});
};
