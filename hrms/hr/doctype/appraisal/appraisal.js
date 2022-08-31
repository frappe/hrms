// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt
frappe.provide("hrms");

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
		const feedbacks = new hrms.Feedback({
			frm: frm,
			feedback_wrapper: $(frm.fields_dict.feedback_html.wrapper),
		});
		feedbacks.refresh();
	},

	setup_chart: function(frm) {
		let labels = [];
		let maximum_scores = [];
		let scores = [];

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
				colors: ["#4CA746", "#98D85B"],
				type: "bar"
			});
		}
	}

});

hrms.Feedback = class Feedback {
	constructor(opts) {
		$.extend(this, opts);
	}

	refresh() {
		var me = this;
		this.feedback_wrapper.find(".notes-section").remove();

		frappe.call({
			method: "hrms.hr.doctype.appraisal.appraisal.get_feedbacks",
			args: {
				employee: me.frm.doc.employee
			},
			callback: function(r) {
				if (!r.exc) {
					let feedbacks = r.message || [];
					feedbacks.sort(
						function(a, b) {
							return new Date(b.added_on) - new Date(a.added_on);
						}
					);

					let feedback_html = frappe.render_template("feedback", {
						feedbacks: feedbacks
					});
					$(feedback_html).appendTo(me.feedback_wrapper);

					$(".notes-section").find(".new-note-btn").on("click", function() {
						me.add_feedback(this);
					});

					$(".notes-section").find(".edit-note-btn").on("click", function() {
						me.edit_feedback(this);
					});

					$(".notes-section").find(".delete-note-btn").on("click", function() {
						me.delete_feedback(this);
					});
				}
			}
		});
	}


	add_feedback () {
		let me = this;
		let _add_feedback = () => {
			this.data = [];
			const dialog = new frappe.ui.Dialog({
				title: __("Add Feedback"),
				fields: [
					{
						"label": "Feedback",
						"fieldname": "feedback",
						"fieldtype": "Text Editor",
						"reqd": 1,
						"enable_mentions": true,
					},
					{
						"label": "KRA Rating",
						"fieldtype": "Table",
						"fieldname": "kra_rating",
						"cannot_add_rows": true,
						"data": this.data,
						get_data: () => {
							return this.data;
						},
						"fields": [
							{
								"fieldname": "kra",
								"fieldtype": "Link",
								"in_list_view": 1,
								"label": "KRA",
								"options": "KRA",
								"reqd": 1
							},
							{
								"fieldname": "per_weightage",
								"fieldtype": "Percent",
								"in_list_view": 1,
								"label": "Weightage"
							},
							{
								"fieldname": "rating",
								"fieldtype": "Rating",
								"in_list_view": 1,
								"label": "Rating"
							}
						]
					}
				],
				primary_action: function() {
					var data = dialog.get_values();
					frappe.call({
						method: "add_feedback",
						doc: me.frm.doc,
						args: {
							feedback: data.feedback,
							kra_rating: data.kra_rating
						},
						freeze: true,
						callback: function(r) {
							if (!r.exc) {
								me.frm.refresh_field("feedbacks_table");
								me.refresh();
							}
							dialog.hide();
						}
					});
				},
				primary_action_label: __("Add")
			});

			frappe.call({
				"method": "hrms.hr.doctype.performance_feedback.performance_feedback.get_kra",
				args: {
					employee: me.frm.doc.employee
				},
				callback: function(data) {
					data.message.goals.forEach(item => {
						dialog.fields_dict.kra_rating.df.data.push({
							"kra": item.kra,
							"per_weightage": item.per_weightage
						});
						this.data = dialog.fields_dict.kra_rating.df.data;
						dialog.fields_dict.kra_rating.grid.refresh();
					})
				}
			});
			dialog.show();
		};
		$(".new-note-btn").click(_add_feedback);
	}

	edit_feedback (edit_btn) {
		var me = this;
		let row = $(edit_btn).closest(".comment-content");
		let row_id = row.attr("name");
		let row_content = $(row).find(".content").html();
		if (row_content) {
			var d = new frappe.ui.Dialog({
				title: __("Edit Feedback"),
				fields: [
					{
						"label": "Feedback",
						"fieldname": "feedback",
						"fieldtype": "Text Editor",
						"reqd": 1,
						"enable_mentions": true,
					}
				],
				primary_action: function() {
					var data = d.get_values();
					frappe.call({
						method: "edit_feedback",
						doc: me.frm.doc,
						args: {
							feedback: data.feedback,
							row_id: row_id
						},
						freeze: true,
						callback: function(r) {
							if (!r.exc) {
								me.frm.refresh_field("feedbacks_table");
								me.refresh();
							}
							d.hide();
						}
					});
				},
				primary_action_label: __("Done")
			});
			d.show();
		}
	}

	delete_feedback (delete_btn) {
		var me = this;
		let row_id = $(delete_btn).closest(".comment-content").attr("name");
		frappe.call({
			method: "delete_feedback",
			doc: me.frm.doc,
			args: {
				row_id: row_id
			},
			freeze: true,
			callback: function(r) {
				if (!r.exc) {
					me.frm.refresh_field("feedbacks_table");
					me.refresh();
				}
			}
		});
	}
};
