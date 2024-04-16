hrms.appraisal_utils = {
	set_autocompletions_for_final_score_formula: async function (frm) {
		const autocompletions = [
			{
				value: "goal_score",
				score: 8,
				meta: "Goal field",
			},
			{
				value: "average_feedback_score",
				score: 8,
				meta: "Appraisal field",
			},
			{
				value: "self_appraisal_score",
				score: 8,
				meta: "Apraisal field",
			},
		]

		const doctypes = [
			"Employee",
			"Appraisal Cycle"
		];

		await Promise.all(doctypes.map((doctype) =>
			frappe.model.with_doctype(doctype, () => {
				autocompletions.push(
					...frappe.get_meta(doctype).fields.map((f) => ({
						value: f.fieldname,
						score: 8,
						meta: __("{0} Field", [doctype]),
					}))
				);
			})
		))
		frm.set_df_property("final_score_formula", "autocompletions", autocompletions);

	},
};
