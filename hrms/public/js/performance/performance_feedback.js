
frappe.provide("hrms");

hrms.PerformanceFeedback = class PerformanceFeedback {
	constructor({ frm, wrapper }) {
		this.frm = frm;
		this.wrapper = wrapper;
	}

	refresh() {
		this.prepare_dom();
		this.setup_feedback_view();
	}

	prepare_dom() {
		this.wrapper.find(".feedback-section").remove();
	}

	setup_feedback_view() {
		frappe.run_serially([
			() => this.get_feedback_history(),
			(data) => this.render_feedback_history(data),
			() => this.setup_actions(),
		])
	}

	get_feedback_history() {
		let me = this;

		return new Promise(resolve => {
			frappe.call({
				method: "hrms.hr.doctype.appraisal.appraisal.get_feedback_history",
				args: {
					employee: me.frm.doc.employee,
					appraisal: me.frm.doc.name
				}
			}).then(r => resolve(r.message));
		});
	}

	async render_feedback_history(data) {
		const { feedback_history, reviews_per_rating } = data || {};
		const perms = await this.get_permissions();

		const feedback_html = frappe.render_template("performance_feedback_history", {
			feedback_history: feedback_history,
			average_feedback_score: this.frm.doc.avg_feedback_score,
			reviews_per_rating: reviews_per_rating,
			permissions: perms
		});

		$(feedback_html).appendTo(this.wrapper);
	}

	setup_actions() {
		let me = this;

		$(".new-feedback-btn").click(() => {
			me.add_feedback();
		});

		$(".feedback-section").find(".view-feedback-btn").on("click", function() {
			me.view_feedback(this);
		});

		$(".feedback-section").find(".edit-feedback-btn").on("click", function() {
			me.edit_feedback(this);
		});

		$(".feedback-section").find(".delete-feedback-btn").on("click", function() {
			me.delete_feedback(this);
		});
	}

	add_feedback() {
		frappe.run_serially([
			() => this.get_feedback_criteria_data(),
			(criteria_data) => this.show_add_feedback_dialog(criteria_data),
		]);
	}

	get_feedback_criteria_data() {
		let me = this;

		return new Promise(resolve => {
			frappe.db.get_doc("Appraisal Template", me.frm.doc.appraisal_template)
				.then(({ rating_criteria }) => {
					const criteria_list = [];
					rating_criteria.forEach((entry) => {
						criteria_list.push({
							"criteria": entry.criteria,
							"per_weightage": entry.per_weightage,
						})
					});
					resolve(criteria_list);
				});
		});
	}

	show_add_feedback_dialog(criteria_data) {
		let me = this;

		const dialog = new frappe.ui.Dialog({
			title: __("Add Feedback"),
			fields: me.get_feedback_dialog_fields(criteria_data),
			primary_action: function() {
				const data = dialog.get_values();

				frappe.call({
					method: "add_feedback",
					doc: me.frm.doc,
					args: {
						feedback: data.feedback,
						feedback_ratings: data.feedback_ratings
					},
					freeze: true,
					callback: function(r) {
						if (!r.exc) {
							me.refresh();
							frappe.show_alert({
								message: __("Feedback {0} added successfully", [r.message.bold()]),
								indicator: "green",
							});
						}
						dialog.hide();
						this.frm.refresh();
					}
				});
			},
			primary_action_label: __("Add")
		});

		dialog.show();
	};

	get_feedback_dialog_fields(criteria_data) {
		return [
			{
				label: "Feedback",
				fieldname: "feedback",
				fieldtype: "Text Editor",
				reqd: 1,
				enable_mentions: true,
			},
			{
				label: "Feedback Rating",
				fieldtype: "Table",
				fieldname: "feedback_ratings",
				cannot_add_rows: true,
				data: criteria_data,
				fields: [
					{
						fieldname: "criteria",
						fieldtype: "Link",
						in_list_view: 1,
						label: "Criteria",
						options: "Employee Feedback Criteria",
						reqd: 1
					},
					{
						fieldname: "per_weightage",
						fieldtype: "Percent",
						in_list_view: 1,
						label: "Weightage"
					},
					{
						fieldname: "rating",
						fieldtype: "Rating",
						in_list_view: 1,
						label: "Rating"
					}
				]
			}
		];
	}

	view_feedback(view_btn) {
		const row_id = $(view_btn).closest(".feedback-content").attr("data-name");
		frappe.set_route("Form", "Employee Performance Feedback", row_id);
	}

	edit_feedback(edit_btn) {
		let me = this;

		const row = $(edit_btn).closest(".feedback-content");
		const row_id = row.attr("data-name");
		const row_content = $(row).find(".feedback").html();

		const dialog = new frappe.ui.Dialog({
			title: __("Edit Feedback"),
			fields: [
				{
					"label": "Feedback",
					"fieldname": "feedback",
					"fieldtype": "Text Editor",
					"reqd": 1,
					"enable_mentions": true,
					"default": row_content
				}
			],
			primary_action: function() {
				const data = dialog.get_values();

				frappe.call({
					method: "edit_feedback",
					doc: me.frm.doc,
					args: {
						feedback: data.feedback,
						name: row_id
					},
					freeze: true,
					callback: function(r) {
						if (!r.exc) {
							me.refresh();
							frappe.show_alert({
								message: __("Feedback {0} updated successfully", [r.message.bold()]),
								indicator: "green",
							});
						}
						dialog.hide();
						this.frm.refresh();
					}
				});
			},
			primary_action_label: __("Update")
		});

		dialog.show();
	}

	delete_feedback(delete_btn) {
		let me = this;
		const row_id = $(delete_btn).closest(".feedback-content").attr("data-name");

		frappe.call({
			method: "delete_feedback",
			doc: me.frm.doc,
			args: {
				name: row_id
			},
			freeze: true,
			callback: function(r) {
				if (!r.exc) {
					me.refresh();
					frappe.show_alert({
						message: __("Feedback {0} deleted successfully", [r.message.bold()]),
						indicator: "green",
					});
				}
			}
		});
	}

	async get_permissions() {
		const is_employee = (
			await frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
		)?.message?.name || false;

		return {
			can_create: (is_employee && frappe.model.can_create("Employee Performance Feedback")),
			can_write: frappe.model.can_write("Employee Performance Feedback"),
			can_delete: frappe.model.can_delete("Employee Performance Feedback"),
		}
	}
};
