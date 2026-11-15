// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// For license information, please see license.txt

// for communication
cur_frm.email_field = "email_id";

frappe.ui.form.on("Job Applicant", {
	setup: function (frm) {
		frm.make_methods = {
			Employee: () =>
				frappe.model.open_mapped_doc({
					method: "hrms.hr.doctype.job_applicant.job_applicant.make_employee",
					frm: frm,
				}),
		};
	},

	refresh: function (frm) {
		frm.set_query("job_title", function () {
			return {
				filters: {
					status: "Open",
				},
			};
		});
		frm.events.remember_stage(frm);
		frm.events.add_hold_menu_item(frm);
		frm.events.show_indicator(frm);
		frm.events.show_resume(frm);
		frm.events.create_custom_buttons(frm);
		frm.events.get_interview_for_dashboard(frm);
		frm.events.show_stage_headline(frm);

		if (!frm.toolbar.page.wrapper.find(".prev-doc").length) {
			frm.toolbar.make_navigation();
		}
	},

	// one control moves the applicant: the same rule as dropping the card on the Hiring Pipeline board
	stage: async function (frm) {
		const to = frm.doc.stage;
		const from = frm.stage_previous;
		if (!to || to === from) return;

		const is_plain_move = ["Applied", "Shortlisted"].includes(to);
		if (frm.doc.__islocal) {
			if (is_plain_move) return (frm.stage_previous = to);
			frm.events.revert_stage(frm, from, false);
			return frappe.msgprint(__("Save the applicant first."));
		}
		if (is_plain_move) return (frm.stage_previous = to);

		const has_other_edits = frm.events.has_unsaved_edits(frm);
		frm.events.revert_stage(frm, from, has_other_edits);
		if (
			has_other_edits &&
			!(await frm.save().then(
				() => true,
				() => false,
			))
		)
			return;

		const applicant = {
			name: frm.doc.name,
			applicant_name: frm.doc.applicant_name,
			designation: frm.doc.designation,
		};
		// a failed step has already shown its error; the stage stays where it was
		const result = await hrms.hiring
			.move_to_stage(applicant, to, { on_undo: () => frm.reload_doc() })
			.catch(() => "cancel");
		if (result === "done") return frm.reload_doc();
		if (result === "move") frm.set_value("stage", to).then(() => (frm.stage_previous = to));
	},

	// puts the stage back without a change event; the form is clean again unless it had other edits
	revert_stage: function (frm, stage, is_dirty) {
		frm.doc.stage = stage;
		frm.refresh_field("stage");
		if (is_dirty) return;
		frm.doc.__unsaved = 0;
		frm.toolbar.refresh();
		frm.events.show_indicator(frm);
	},

	remember_stage: function (frm) {
		frm.stage_previous = frm.saved_stage = frm.doc.stage;
		frm.saved_values = frm.events.get_plain_values(frm);
	},

	get_plain_values: function (frm) {
		return Object.fromEntries(
			Object.entries(frm.doc).filter(
				([key, value]) =>
					!key.startsWith("__") &&
					key !== "stage" &&
					(value === null || typeof value !== "object"),
			),
		);
	},

	// edits besides the stage being picked now, including an earlier plain stage change
	has_unsaved_edits: function (frm) {
		if (frm.stage_previous !== frm.saved_stage) return true;
		const values = frm.events.get_plain_values(frm);
		return Object.keys(values).some(
			(key) => (values[key] ?? "") !== (frm.saved_values[key] ?? ""),
		);
	},

	add_hold_menu_item: function (frm) {
		const can_hold = !["Rejected", "Hired"].includes(frm.doc.stage);
		const is_on_hold = frm.doc.status === "Hold";
		if (frm.doc.__islocal || !frm.perm[0]?.write || !(can_hold || is_on_hold)) return;
		frm.page.add_menu_item(is_on_hold ? __("Resume") : __("Put on hold"), async () => {
			await frm.call(is_on_hold ? "resume" : "put_on_hold");
			frm.reload_doc();
		});
	},

	// the pill is the stage, in the same colours as the applicant list
	show_indicator: function (frm) {
		if (frm.is_dirty() || frm.doc.__islocal || !frm.doc.stage) return;
		const { label, theme } = hrms.hiring.get_stage_badge(frm.doc);
		frm.page.set_indicator(label, theme);
	},

	show_resume: function (frm) {
		frm.toggle_display("resume_preview_html", false);
		frm.toggle_display("open_resume_button", false);
		if (frm.doc.resume_link) {
			const src_url = frappe.utils.escape_html(frm.doc.resume_link);
			if (src_url.endsWith(".pdf")) {
				frm.toggle_display("resume_preview_html", true);
				frm.events.show_pdf_preview(frm, src_url);
			} else {
				frm.toggle_display("open_resume_button", true);
			}
		}
	},
	show_pdf_preview: function (frm, src_url) {
		let $preview = $(`<div class="img_preview" style="padding-bottom:12px;">
			<object style="background:#323639;" width="100%">
				<embed
				style="background:#323639;"
				width="100%"
				height="1000px"
				src="${src_url}" type="application/pdf"
				>
			</object>
			</div>`);
		frm.get_field("resume_preview_html").$wrapper.html($preview);
	},
	open_resume_button: function (frm) {
		window.open(frm.doc.resume_link, "_blank", "noopener");
	},
	create_custom_buttons: function (frm) {
		if (!frm.doc.__islocal) {
			if (frm.doc.status == "Open") {
				frm.add_custom_button(__("Shortlist"), () => {
					frm.set_value("status", "Shortlisted");
					frm.save();
					frm.refresh();
				});
				frm.add_custom_button(__("Reject"), () => {
					frm.set_value("status", "Rejected");
					frm.save();
					frm.refresh();
				});
			}
			if (frm.doc.status !== "Rejected" && frm.doc.status !== "Accepted") {
				frm.add_custom_button(__("Schedule Interview"), () => {
					frm.events.show_schedule_interview_dialog(frm);
				});
			}
		}

		if (frm.doc.__islocal) return;

		const onload = frm.doc.__onload || {};
		if (onload.employee) {
			frm.add_custom_button(__("View Employee"), function () {
				frappe.set_route("Form", "Employee", onload.employee);
			});
		}

		if (!["Shortlisted", "Accepted"].includes(frm.doc.status)) return;

		if (onload.job_offer) {
			$('[data-doctype="Employee Onboarding"]').find("button").show();
			$('[data-doctype="Job Offer"]').find("button").hide();
			frm.add_custom_button(__("View Job Offer"), function () {
				frappe.set_route("Form", "Job Offer", onload.job_offer);
			});
		} else {
			$('[data-doctype="Employee Onboarding"]').find("button").hide();
			$('[data-doctype="Job Offer"]').find("button").show();
			frm.add_custom_button(__("Create Job Offer"), function () {
				frappe.route_options = {
					job_applicant: frm.doc.name,
					applicant_name: frm.doc.applicant_name,
					designation: frm.doc.designation,
				};
				frappe.new_doc("Job Offer");
			});
		}
	},

	show_stage_headline: function (frm) {
		if (frm.doc.__islocal || !frm.doc.job_title) return;

		frappe.call({
			method: "hrms.hr.page.hiring.hiring.get_applicant_stage",
			type: "GET",
			args: { job_applicant: frm.doc.name },
			silent: true,
			callback: (r) => {
				const data = r.message;
				if (!data || !data.stage) return;

				const parts = [];
				if (data.fact) parts.push(frappe.utils.escape_html(data.fact));
				// the form can refresh twice before either call returns; keep one headline
				frm.stage_headline?.remove();
				frm.stage_headline = parts.length
					? frm.dashboard.set_headline(parts.join(" · "))
					: null;
			},
			error: () => {},
		});
	},

	get_interview_for_dashboard: function (frm) {
		frm.toggle_display("interview_summary_section", false);
		if (frm.doc.__islocal) return;

		frappe.call({
			method: "hrms.hr.doctype.job_applicant.job_applicant.get_interview_details",
			args: {
				job_applicant: frm.doc.name,
			},
			callback: function (r) {
				if (r.message) {
					frm.events.make_dashboard(frm, r.message);
				}
			},
		});
	},

	make_dashboard: function (frm, interviews) {
		const can_open = frappe.model.can_read("Interview");
		const items = interviews.map((interview) => ({
			id: interview.name,
			title: interview.interview_type,
			subtitle: hrms.format_interview_time(interview.scheduled_on, interview.from_time),
			href: can_open
				? `/desk/${frappe.router.slug("Interview")}/${encodeURIComponent(interview.name)}`
				: undefined,
			controls: () => [
				interview.average_rating > 0
					? frappe.ui.rating({ value: interview.average_rating, step: 0.5, size: "xs" })
					: null,
				frappe.ui.badge(hrms.hiring.get_interview_badge(interview)),
			],
		}));
		frm.fields_dict.interview_summary_html.$wrapper
			.addClass("mb-4")
			.empty()
			.append(new frappe.ui.ItemList({ items }).$el);
		frm.toggle_display("interview_summary_section", true);
	},

	show_schedule_interview_dialog: function (frm) {
		hrms.schedule_interview({
			job_applicant: frm.doc.name,
			designation: frm.doc.designation,
			on_scheduled: () => {
				frappe.show_alert({
					message: __("Interview scheduled successfully"),
					indicator: "green",
				});
				frm.events.get_interview_for_dashboard(frm);
			},
		});
	},
});
