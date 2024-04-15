hrms.appraisal_utils = {
	set_autocompletions_for_final_score_formula: function (frm) {
		const autocompletions = [];
		fields_data = [
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
		];
		autocompletions.push(fields_data);
		frm.set_df_property(
			"final_score_formula",
			"autocompletions",
			autocompletions
		);
	},
};
