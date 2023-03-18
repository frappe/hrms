// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on("Appraisal", {
	refresh: function(frm) {
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__("View Goals"), function() {
				frappe.route_options = {
					company: frm.doc.company,
					employee: frm.doc.employee,
					appraisal_cycle: frm.doc.appraisal_cycle,
				};
				frappe.set_route("Tree", "Goal");
			});

			frm.trigger("show_feedback_history");
			frm.trigger("setup_chart");
		}

		frm.sidebar.image_wrapper.find(".sidebar-image-actions").addClass("hide");
	},

	appraisal_template: function(frm) {
		if (frm.doc.appraisal_template) {
			frm.call("set_kras_and_rating_criteria", () => {
				frm.refresh_field("appraisal_kra");
				frm.refresh_field("feedback_ratings");
			});
		}
	},

	show_feedback_history: function(frm) {
		frappe.require("performance.bundle.js", () => {
			const feedback_history = new hrms.PerformanceFeedback({
				frm: frm,
				wrapper: $(frm.fields_dict.feedback_html.wrapper),
			});
			feedback_history.refresh();
		});
	},

	setup_chart: function(frm) {
		const labels = [];
		const maximum_scores = [];
		const scores = [];

		$.each(frm.doc.appraisal_kra, function(_i, e) {
			labels.push(e.kra);
			maximum_scores.push(e.per_weightage || 0);
			scores.push(e.goal_score || 0);
		});

		if (labels.length && maximum_scores.length && scores.length) {
			frm.dashboard.render_graph({
				data: {
					labels: labels,
					datasets: [
						{
							name: "Maximum Score",
							chartType: "bar",
							values: maximum_scores,
						},
						{
							name: "Score Obtained",
							chartType: "bar",
							values: scores,
						}
					]
				},
				title: __("Scores"),
				height: 300,
				type: "bar",
				colors: ["blue", "green"]
			});
		}
	}
});
