// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on("Appraisal", {
	refresh: function(frm) {
		if (!frm.doc._islocal) {
			frm.add_custom_button(__("View Goals"), function() {
				frappe.route_options = {
					company: frm.doc.company,
					employee: frm.doc.employee,
				};
				frappe.set_route("Tree", "Goal");
			});

			frm.trigger("show_feedbacks");
			frm.trigger("setup_chart");
		}

		frm.sidebar.image_wrapper.find(".sidebar-image-actions").addClass("hide");
	},

	kra_template: function(frm) {
		if (frm.doc.kra_template) {
			frappe.call({
				"method": "frappe.client.get",
				args: {
					doctype: "Appraisal Template",
					name: frm.doc.kra_template
				},
				callback: function(data) {
					frm.doc.appraisal_kra = [];
					$.each(data.message.goals, function(_i, e) {
						let entry = frm.add_child("appraisal_kra");
						entry.kra = e.kra;
						entry.per_weightage = e.per_weightage;

						entry = frm.add_child("kra_rating");
						entry.kra = e.kra;
						entry.per_weightage = e.per_weightage;
					});
					refresh_field("appraisal_kra");
				}
			});
		}
	},

	show_feedbacks: function(frm) {
		frappe.require("performance.bundle.js", () => {
			const feedbacks = new hrms.PerformanceFeedback({
				frm: frm,
				feedback_wrapper: $(frm.fields_dict.feedback_html.wrapper),
			});
			feedbacks.refresh();
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
