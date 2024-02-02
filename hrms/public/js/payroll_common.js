hrms.payroll_common = {
	get_autocompletions_for_condition_and_formula: function (frm) {
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
	},
};
