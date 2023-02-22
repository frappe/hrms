
frappe.provide("hrms");

hrms.PerformanceFeedback = class PerformanceFeedback {
	constructor(opts) {
		$.extend(this, opts);
	}

	refresh() {
		var me = this;
		this.feedback_wrapper.find(".feedback-section").remove();

		frappe.call({
			method: "hrms.hr.doctype.appraisal.appraisal.get_feedbacks",
			args: {
				employee: me.frm.doc.employee,
				appraisal: me.frm.doc.name
			},
			callback: function(r) {
				if (!r.exc) {
					const data = r.message || [];
					const feedbacks = data.feedbacks;

					feedbacks.sort(
						function(a, b) {
							return new Date(b.added_on) - new Date(a.added_on);
						}
					);

					const feedback_html = frappe.render_template("employee_feedbacks", {
						feedbacks: feedbacks,
						average_feedback_score: me.frm.doc.avg_feedback_score,
						reviews_per_rating: data.reviews_per_rating
					});
					$(feedback_html).appendTo(me.feedback_wrapper);

					$(".feedback-section").find(".new-feedback-btn").on("click", function() {
						me.add_feedback(this);
					});

					$(".feedback-section").find(".edit-feedback-btn").on("click", function() {
						me.edit_feedback(this);
					});

					$(".feedback-section").find(".delete-feedback-btn").on("click", function() {
						me.delete_feedback(this);
					});
				}
			}
		});
	}


	add_feedback() {
		const me = this;
		const _add_feedback = () => {
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
					data.message.goals.forEach((item) => {
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

	edit_feedback(edit_btn) {
		const me = this;
		const row = $(edit_btn).closest(".comment-content");
		const row_id = row.attr("name");
		const row_content = $(row).find(".content").html();
		if (row_content) {
			const d = new frappe.ui.Dialog({
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

	delete_feedback(delete_btn) {
		const me = this;
		const row_id = $(delete_btn).closest(".comment-content").attr("name");
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
