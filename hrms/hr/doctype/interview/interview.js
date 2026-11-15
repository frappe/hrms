// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Interview", {
	setup: function (frm) {
		frm.hide_submit_message = true;
	},

	refresh: function (frm) {
		frm.set_query("job_applicant", function () {
			let job_applicant_filters = {
				status: ["!=", "Rejected"],
			};
			if (frm.doc.designation) {
				job_applicant_filters.designation = frm.doc.designation;
			}
			return {
				filters: job_applicant_filters,
			};
		});

		frm.set_query("interviewer", "interview_details", () => ({
			filters: hrms.interviewer_filters(),
		}));

		frm.trigger("add_custom_buttons");
		if (frm.doc.__islocal) return;

		frappe.run_serially([
			() => frm.trigger("load_skills_average_rating"),
			() => frm.trigger("load_feedback"),
		]);
	},

	add_custom_buttons: async function (frm) {
		frm.owes_feedback = false;
		if (frm.doc.docstatus === 2 || frm.doc.__islocal) return;

		if (frm.doc.docstatus === 1 && frm.doc.status === "Cleared") {
			frm.events.add_create_job_offer_button(frm);
		}

		if (frm.doc.status === "Pending") {
			frm.add_custom_button(
				__("Reschedule Interview"),
				function () {
					frm.events.show_reschedule_dialog(frm);
					frm.refresh();
				},
				__("Actions"),
			);
		}

		const is_awaiting_result = ["Pending", "Under Review"].includes(frm.doc.status);
		let feedback_count = 0;
		if (is_awaiting_result) {
			feedback_count = await frappe.db.count("Interview Feedback", {
				filters: { interview: frm.doc.name, docstatus: 1 },
			});
			if (frm.doc.docstatus === 0 && feedback_count) frm.events.add_decision_buttons(frm);
		}

		const has_submitted_feedback = await frappe.db.get_value(
			"Interview Feedback",
			{
				interviewer: frappe.session.user,
				interview: frm.doc.name,
				docstatus: ["!=", 2],
			},
			"name",
		);

		if (has_submitted_feedback?.message?.name) return;

		const allow_feedback_submission = frm.doc.interview_details.some(
			(interviewer) => interviewer.interviewer === frappe.session.user,
		);

		if (allow_feedback_submission) {
			frm.page.set_primary_action(__("Submit Feedback"), () => {
				frm.events.submit_feedback(frm);
			});
			frm.owes_feedback = true;
			if (frm.feedback) frm.events.render_feedback(frm);
		} else if (is_awaiting_result && !feedback_count) {
			frm.set_intro(__("Only interviewers on the panel can add feedback."), "blue");
		}
	},

	add_decision_buttons: function (frm) {
		frm.set_intro(
			__("Feedback is in. Mark the interview Cleared or Rejected, then submit it."),
			"blue",
		);
		["Cleared", "Rejected"].forEach((status) =>
			frm.add_custom_button(
				__(status),
				async () => {
					await frm.set_value("status", status);
					frm.save();
				},
				__("Mark as"),
			),
		);
	},

	add_create_job_offer_button: async function (frm) {
		// interviewers without offer access shouldn't hit a permission popup
		if (!frappe.model.can_create("Job Offer")) return;
		const { message: offer } = await frappe.db.get_value(
			"Job Offer",
			{
				job_applicant: frm.doc.job_applicant,
				docstatus: ["<", 2],
				status: ["!=", "Cancelled"],
			},
			"name",
		);
		if (offer?.name) return;

		const { message: applicant } = await frappe.db.get_value(
			"Job Applicant",
			frm.doc.job_applicant,
			["applicant_name", "designation"],
		);
		frm.add_custom_button(__("Create offer"), () =>
			frappe.new_doc("Job Offer", {
				job_applicant: frm.doc.job_applicant,
				applicant_name: applicant?.applicant_name,
				designation: applicant?.designation,
			}),
		);
	},

	submit_feedback: function (frm) {
		if (frm.doc.scheduled_on && frm.doc.scheduled_on > frappe.datetime.get_today()) {
			frappe.msgprint({
				title: __("Too early for feedback"),
				message: __("You can add feedback from {0}, the interview date.", [
					frappe.datetime.str_to_user(frm.doc.scheduled_on),
				]),
				indicator: "orange",
			});
			return;
		}
		frappe.call({
			method: "hrms.hr.doctype.interview.interview.get_expected_skill_set",
			args: {
				interview_type: frm.doc.interview_type,
			},
			callback: function (r) {
				frm.events.show_feedback_dialog(frm, r.message);
			},
		});
	},

	show_reschedule_dialog: function (frm) {
		hrms.reschedule_interview({
			interview: frm.doc,
			on_rescheduled: () => frm.refresh(),
		});
	},

	show_feedback_dialog: function (frm, skills) {
		frappe.require("interview.bundle.js", () =>
			hrms.open_interview_feedback({
				interview: frm.doc,
				skills,
				on_submitted: () => frm.refresh(),
			}),
		);
	},

	interview_type: function (frm) {
		frm.trigger("set_applicable_interviewers");
	},

	job_applicant: function (frm) {
		if (frm.doc.job_applicant && !frm.doc.designation) {
			frm.add_fetch("job_applicant", "designation", "designation");
		}
	},

	set_applicable_interviewers(frm) {
		frappe.call({
			method: "hrms.hr.doctype.interview.interview.get_interviewers",
			args: {
				interview_type: frm.doc.interview_type || "",
			},
			callback: function (r) {
				frm.clear_table("interview_details");
				r.message.forEach((interviewer) =>
					frm.add_child("interview_details", interviewer),
				);
				refresh_field("interview_details");
			},
		});
	},

	load_skills_average_rating(frm) {
		return frappe
			.call({
				method: "hrms.hr.doctype.interview.interview.get_skill_wise_average_rating",
				args: { interview: frm.doc.name },
				silent: true,
			})
			.then((r) => {
				frm.skills_average_rating = r.message || [];
			})
			.catch(() => {
				frm.skills_average_rating = [];
			});
	},

	load_feedback(frm) {
		return frappe
			.call({
				method: "hrms.hr.doctype.interview.interview.get_feedback",
				args: { interview: frm.doc.name },
				silent: true,
			})
			.then((r) => {
				frm.feedback = r.message || [];
			})
			.catch(() => {
				frm.feedback = [];
			})
			.then(() => {
				frm.events.render_feedback(frm);
			});
	},

	get_panel(frm) {
		const reviews = Object.fromEntries(frm.feedback.map((f) => [f.user, f]));
		const users = new Set([
			...frm.doc.interview_details.map((row) => row.interviewer),
			...Object.keys(reviews),
		]);
		return [...users].map((user) => ({
			user,
			name: reviews[user]?.reviewer_name || frappe.user_info(user).fullname || user,
			image: frappe.user_info(user).image,
			result: reviews[user]?.result,
			score: reviews[user]?.total_score,
		}));
	},

	render_feedback(frm) {
		frappe.require("interview.bundle.js", () => {
			const wrapper = $(frm.fields_dict.feedback_html.wrapper);
			const panel = frm.events.get_panel(frm);
			const feedback_html = frappe.render_template("interview_feedback", {
				feedbacks: frm.feedback,
				average_rating: Math.round(frm.doc.average_rating * 50 + 1e-9) / 10,
				skills_average_rating: frm.skills_average_rating || [],
				panel,
				submitted_count: frm.feedback.length,
				owes_feedback: frm.owes_feedback,
			});
			wrapper.empty();
			const $feedback = $(feedback_html).appendTo(wrapper);
			$feedback
				.find(".if-submit-feedback")
				.on("click", () => frm.events.submit_feedback(frm));
			if (frm.owes_feedback && frm.feedback.length) {
				const on_panel = frm.doc.interview_details.map((row) => row.interviewer);
				const given = new Set(
					frm.feedback.map((f) => f.user).filter((u) => on_panel.includes(u)),
				).size;
				frappe.ui
					.alert({
						title: __("Your feedback is pending"),
						description: __("{0} of {1} on the panel have added theirs", [
							given,
							on_panel.length,
						]),
						footer: frappe.ui.button({
							label: __("Submit feedback"),
							variant: "outline",
							onclick: () => frm.events.submit_feedback(frm),
						}),
						css_class: "if-pending",
					})
					.prependTo($feedback);
			}
			$feedback.find("[data-open-feedback]").each(function () {
				frappe.ui.tooltip($(this), { text: __("Open feedback") });
			});
		});
	},
});
