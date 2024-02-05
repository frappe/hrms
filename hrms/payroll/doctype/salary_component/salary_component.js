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
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__("Salary Structure"), () => {
				frm.trigger("create_salary_structure");
			}, __("Create"));
=======
		hrms.payroll_common.get_autocompletions_for_condition_and_formula(frm);
=======
		hrms.payroll_common.set_autocompletions_for_condition_and_formula(frm);
>>>>>>> c6817a203 (feat: setup autocompletions for salary structure fields)

		if (!frm.doc.__islocal) {
			frm.trigger("add_update_structure_button");
			frm.add_custom_button(
				__("Salary Structure"),
				() => {
					frm.trigger("create_salary_structure");
				},
				__("Create")
			);
>>>>>>> cbf31f93e (chore: commonify condition/formula autocompletions)
		}
=======
		frm.trigger("setup_autocompletions");
<<<<<<< HEAD
>>>>>>> 0625e7bc2 (feat: add autocompletion to code fields)
=======
		if (!frm.doc.__islocal) {
			frm.trigger("add_update_structure_button");
		}
>>>>>>> 5c5f91b36 (feat: add option to sync formula and condition for existing structures)
	},

	is_flexible_benefit: function (frm) {
		if (frm.doc.is_flexible_benefit) {
			set_value_for_condition_and_formula(frm);
			frm.set_value("formula", "");
			frm.set_value("amount", 0);
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
		}
	},

	variable_based_on_taxable_salary: function (frm) {
		if (frm.doc.variable_based_on_taxable_salary) {
			set_value_for_condition_and_formula(frm);
		}
	},

	create_separate_payment_entry_against_benefit_claim: function (frm) {
		if (frm.doc.create_separate_payment_entry_against_benefit_claim) {
			frm.set_df_property("accounts", "reqd", 1);
			frm.set_value("only_tax_impact", 0);
		} else {
			frm.set_df_property("accounts", "reqd", 0);
		}
	},

	only_tax_impact: function (frm) {
		if (frm.only_tax_impact) {
			frm.set_value("create_separate_payment_entry_against_benefit_claim", 0);
		}
	},

<<<<<<< HEAD
<<<<<<< HEAD
	create_salary_structure: function (frm) {
		frappe.model.with_doctype("Salary Structure", () => {
			const salary_structure = frappe.model.get_new_doc("Salary Structure");
			const salary_detail = frappe.model.add_child(
				salary_structure,
				frm.doc.type === "Earning" ? "earnings" : "deductions"
			);
			salary_detail.salary_component = frm.doc.name;
			frappe.set_route("Form", "Salary Structure", salary_structure.name);
		});
=======
	setup_autocompletions: function (frm) {
<<<<<<< HEAD
		frappe.db
			.get_list("Salary Component", { fields: ["salary_component_abbr"] })
			.then((salary_components) => {
				const autocompletions = salary_components.map((d) => ({
					value: d.salary_component_abbr,
					score: 10,
					meta: "Salary Component",
				}));
				frappe.db.get_doc("DocType", "Employee").then((employee_doc) => {
					const employee_fields = employee_doc.fields.map((f) => ({
						value: f.fieldname,
						score: 9,
						meta: "Employee Field",
					}));
					autocompletions.push(...employee_fields);
					frm.set_df_property("condition", "autocompletions", autocompletions);
					frm.set_df_property("formula", "autocompletions", autocompletions);
				});
			});
>>>>>>> 0625e7bc2 (feat: add autocompletion to code fields)
=======
		const autocompletions = [];
		frappe.run_serially([
			...["Employee", "Salary Structure", "Salary Slip"].map((doctype) =>
				frappe.model.with_doctype(doctype, () => {
					autocompletions.push(
						...frappe.get_meta(doctype).fields.map((f) => ({
							value: f.fieldname,
							score: 9,
							meta: __("{0} Field", [doctype]),
						}))
					);
				})
			),
			() => {
				frappe.db
					.get_list("Salary Component", {
						fields: ["salary_component_abbr"],
					})
					.then((salary_components) => {
						autocompletions.push(
							...salary_components.map((d) => ({
								value: d.salary_component_abbr,
								score: 10,
								meta: __("Salary Component"),
							}))
						);
						frm.set_df_property(
							"condition",
							"autocompletions",
							autocompletions
						);
						frm.set_df_property("formula", "autocompletions", autocompletions);
					});
			},
		]);
>>>>>>> 6c06213b6 (feat: add autocompletions for Salary Structure and Salary Slip fields)
	},

=======
>>>>>>> cbf31f93e (chore: commonify condition/formula autocompletions)
	add_update_structure_button: function (frm) {
		for (const df of ["Condition", "Formula"]) {
			frm.add_custom_button(
				__("Sync {0}", [df]),
				function () {
					frappe
						.call({
							method: "get_structures_to_be_updated",
							doc: frm.doc,
						})
						.then((res) => {
							let msg = __(
								"{0} will be updated for the following Salary Structures: {1}.",
								[df, frappe.utils.comma_and(res.message.map((d) => d.bold()))]
							);
							msg += "<br>";
							msg += __("Are you sure you want to proceed?");
							frappe.confirm(msg, () => {
								frappe
									.call({
										method: "update_salary_structures",
										doc: frm.doc,
										args: {
											structures: res.message,
											field: df.toLowerCase(),
											value: frm.get_field(df.toLowerCase()).value,
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
						});
				},
				__("Update Salary Structures")
			);
		}
<<<<<<< HEAD
=======
	},

	create_salary_structure: function (frm) {
		frappe.model.with_doctype("Salary Structure", () => {
			const salary_structure = frappe.model.get_new_doc("Salary Structure");
			const salary_detail = frappe.model.add_child(
				salary_structure,
				frm.doc.type === "Earning" ? "earnings" : "deductions"
			);
			salary_detail.salary_component = frm.doc.name;
			frappe.set_route("Form", "Salary Structure", salary_structure.name);
		});
>>>>>>> cbf31f93e (chore: commonify condition/formula autocompletions)
	},
});

var set_value_for_condition_and_formula = function (frm) {
	frm.set_value("formula", null);
	frm.set_value("condition", null);
	frm.set_value("amount_based_on_formula", 0);
	frm.set_value("statistical_component", 0);
	frm.set_value("do_not_include_in_total", 0);
	frm.set_value("depends_on_payment_days", 0);
};
