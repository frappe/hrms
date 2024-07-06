// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Appraisal Cycle", {
	refresh(frm) {
		frm.set_query("department", () => {
			return {
				filters: {
					company: frm.doc.company,
				},
			};
		});

		frm.trigger("show_custom_buttons");
		frm.trigger("show_appraisal_summary");
		frm.trigger("set_autocompletions_for_final_score_formula");
	},

	show_custom_buttons(frm) {
		if (frm.doc.__islocal) return;

		frm.add_custom_button(__("View Goals"), () => {
			frappe.route_options = {
				company: frm.doc.company,
				appraisal_cycle: frm.doc.name,
			};
			frappe.set_route("Tree", "Goal");
		});

		let appraisals_created = frm.doc.__onload?.appraisals_created;

		if (frm.doc.status !== "Completed") {
			if (appraisals_created) {
				frm.add_custom_button(__("Create Appraisals"), () => {
					frm.trigger("create_appraisals");
				});
			} else {
				frm.page.set_primary_action(__("Create Appraisals"), () => {
					frm.trigger("create_appraisals");
				});
			}
		}

		if (frm.doc.status === "Not Started") {
			if (appraisals_created) {
				frm.page.set_primary_action(__("Start"), () => {
					frm.set_value("status", "In Progress");
					frm.save();
				});
			} else {
				frm.add_custom_button(__("Start"), () => {
					frm.set_value("status", "In Progress");
					frm.save();
				});
			}
		} else if (frm.doc.status === "In Progress") {
			if (appraisals_created) {
				frm.page.set_primary_action(__("Mark as Completed"), () => {
					frm.trigger("complete_cycle");
				});
			} else {
				frm.add_custom_button(__("Mark as Completed"), () => {
					frm.trigger("complete_cycle");
				});
			}
		} else if (frm.doc.status === "Completed") {
			frm.add_custom_button(__("Mark as In Progress"), () => {
				frm.set_value("status", "In Progress");
				frm.save();
			});
		}
	},

	set_autocompletions_for_final_score_formula: async (frm) => {
		const autocompletions = [
			{
				value: "goal_score",
				score: 10,
				meta: __("Total Goal Score"),
			},
			{
				value: "average_feedback_score",
				score: 10,
				meta: __("Average Feedback Score"),
			},
			{
				value: "self_appraisal_score",
				score: 10,
				meta: __("Self Appraisal Score"),
			},
		];

		await Promise.all(
			["Employee", "Appraisal Cycle", "Appraisal"].map((doctype) =>
				frappe.model.with_doctype(doctype, () => {
					autocompletions.push(...hrms.get_doctype_fields_for_autocompletion(doctype));
				}),
			),
		);

		frm.set_df_property("final_score_formula", "autocompletions", autocompletions);
	},

	get_employees(frm) {
		frappe.call({
			method: "set_employees",
			doc: frm.doc,
			freeze: true,
			freeze_message: __("Fetching Employees"),
			callback: function () {
				refresh_field("appraisees");
				frm.dirty();
			},
		});
	},

	create_appraisals(frm) {
		frm.call({
			method: "create_appraisals",
			doc: frm.doc,
			freeze: true,
		}).then((r) => {
			if (!r.exc) {
				frm.reload_doc();
			}
		});
	},

	complete_cycle(frm) {
		let msg = __(
			"This action will prevent making changes to the linked appraisal feedback/goals.",
		);
		msg += "<br>";
		msg += __("Are you sure you want to proceed?");

		frappe.confirm(msg, () => {
			frm.call({
				method: "complete_cycle",
				doc: frm.doc,
				freeze: true,
			}).then((r) => {
				if (!r.exc) {
					frm.reload_doc();
				}
			});
		});
	},

	show_appraisal_summary(frm) {
		if (frm.doc.__islocal) return;

		frappe
			.call("hrms.hr.doctype.appraisal_cycle.appraisal_cycle.get_appraisal_cycle_summary", {
				cycle_name: frm.doc.name,
			})
			.then((r) => {
				if (r.message) {
					frm.dashboard.add_indicator(
						__("Appraisees: {0}", [r.message.appraisees]),
						"blue",
					);
					frm.dashboard.add_indicator(
						__("Self Appraisal Pending: {0}", [r.message.self_appraisal_pending]),
						"orange",
					);
					frm.dashboard.add_indicator(
						__("Employees without Feedback: {0}", [r.message.feedback_missing]),
						"orange",
					);
					frm.dashboard.add_indicator(
						__("Employees without Goals: {0}", [r.message.goals_missing]),
						"orange",
					);
				}
			});
	},
});
