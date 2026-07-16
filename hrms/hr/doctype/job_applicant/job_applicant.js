// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// For license information, please see license.txt

// for communication
cur_frm.email_field = "email_id";

frappe.ui.form.on("Job Applicant", {
	refresh: function (frm) {
		frm.set_query("job_title", function () {
			return {
				filters: {
					status: "Open",
				},
			};
		});
		frm.events.show_resume(frm);
		frm.events.create_custom_buttons(frm);
		frm.events.get_interview_for_dashboard(frm);

		if (!frm.toolbar.page.wrapper.find(".prev-doc").length) {
			frm.toolbar.make_navigation();
		}
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

		if (!frm.doc.__islocal && frm.doc.status == "Accepted") {
			if (frm.doc.__onload && frm.doc.__onload.job_offer) {
				$('[data-doctype="Employee Onboarding"]').find("button").show();
				$('[data-doctype="Job Offer"]').find("button").hide();
				frm.add_custom_button(__("View Job Offer"), function () {
					frappe.set_route("Form", "Job Offer", frm.doc.__onload.job_offer);
				});
			} else {
				$('[data-doctype="Employee Onboarding"]').find("button").hide();
				$('[data-doctype="Job Offer"]').find("button").show();
				frm.add_custom_button(__("Create Job Offer"), function () {
					frappe.route_options = {
						job_applicant: frm.doc.name,
						applicant_name: frm.doc.applicant_name,
						designation: frm.doc.job_opening || frm.doc.designation,
					};
					frappe.new_doc("Job Offer");
				});
			}
		}
	},

	get_interview_for_dashboard: function (frm) {
		if (frm.doc.__islocal) return;

		$("div").remove(".form-dashboard-section.custom");
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

	make_dashboard: function (frm, message) {
		frm.dashboard.add_section(
			frappe.render_template("job_applicant_dashboard", {
				data: message.interviews,
				number_of_stars: message.stars,
			}),
			__("Interview Summary"),
		);
	},

	show_schedule_interview_dialog: function (frm) {
		frappe.model.with_doctype("Interview Detail", () => frm.events.show_schedule_dialog(frm));
	},

	show_schedule_dialog: function (frm) {
		let d = new frappe.ui.Dialog({
			title: __("Schedule Interview"),
			fields: [
				{
					label: __("Interview Type"),
					fieldname: "interview_type",
					fieldtype: "Link",
					options: "Interview Type",
					reqd: 1,
					get_query: () => ({
						filters: frm.doc.designation
							? [["designation", "in", [frm.doc.designation, ""]]]
							: [],
					}),
					onchange() {
						const interview_type = d.get_value("interview_type");
						if (!interview_type) return;
						frappe.call({
							method: "hrms.hr.doctype.interview.interview.get_interviewers",
							args: { interview_type },
							callback(r) {
								d.set_value(
									"interviewers",
									(r.message || []).map((i) => ({ interviewer: i.interviewer })),
								);
							},
						});
					},
				},
				{
					label: __("From Time"),
					fieldname: "from_time",
					fieldtype: "Time",
					reqd: 1,
				},
				{ fieldtype: "Column Break" },
				{
					label: __("Scheduled On"),
					fieldname: "scheduled_on",
					fieldtype: "Date",
					reqd: 1,
					default: frappe.datetime.get_today(),
				},
				{
					label: __("To Time"),
					fieldname: "to_time",
					fieldtype: "Time",
					reqd: 1,
				},
				{
					fieldtype: "Section Break",
					label: __("Interviewers"),
				},
				{
					fieldname: "interviewers",
					fieldtype: "Table MultiSelect",
					options: "Interview Detail",
				},
				{
					fieldname: "send_confirmation",
					fieldtype: "Check",
					label: __("Send confirmation email to candidate and interviewers"),
					onchange() {
						d.get_primary_btn().text(
							d.get_value("send_confirmation")
								? __("Schedule & Notify")
								: __("Schedule"),
						);
					},
				},
			],
			primary_action_label: __("Schedule"),
			primary_action(values) {
				if (values.send_confirmation) {
					frappe.db
						.get_value("HR Settings", "HR Settings", [
							"send_interview_confirmation",
							"hiring_sender_email",
						])
						.then((r) => {
							const settings = r.message;
							const hr_settings_link = `<a href="${frappe.utils.get_form_link(
								"HR Settings",
								"HR Settings",
							)}#recruitment_tab" target="_blank">${__("HR Settings")}</a>`;

							if (
								!settings.send_interview_confirmation &&
								!settings.hiring_sender_email
							) {
								frappe.msgprint({
									title: __("Email Not Configured"),
									message: __(
										"Please enable {0} and set a {1} in {2}.",
										[
											frappe.utils.bold(__("Send Interview Confirmation")),
											frappe.utils.bold(__("Hiring Sender Email")),
											hr_settings_link,
										],
									),
									indicator: "orange",
								});
								return;
							} else if (!settings.send_interview_confirmation) {
								frappe.msgprint({
									title: __("Email Not Configured"),
									message: __("Please enable {0} in {1}.", [
										frappe.utils.bold(__("Send Interview Confirmation")),
										hr_settings_link,
									]),
									indicator: "orange",
								});
								return;
							} else if (!settings.hiring_sender_email) {
								frappe.msgprint({
									title: __("Email Not Configured"),
									message: __("Please set a {0} in {1}.", [
										frappe.utils.bold(__("Hiring Sender Email")),
										hr_settings_link,
									]),
									indicator: "orange",
								});
								return;
							}
							frm.events.do_schedule_interview(frm, d, values);
						});
					return;
				}
				frm.events.do_schedule_interview(frm, d, values);
			},
		});
		d.show();
	},

	do_schedule_interview: function (frm, d, values) {
		frappe.call({
			method: "hrms.hr.doctype.job_applicant.job_applicant.schedule_interview",
			args: {
				job_applicant: frm.doc.name,
				interview_type: values.interview_type,
				scheduled_on: values.scheduled_on,
				from_time: values.from_time,
				to_time: values.to_time,
				interviewers: values.interviewers || [],
			},
			callback(r) {
				if (r.message) {
					if (values.send_confirmation) {
						frappe.call({
							method: "hrms.hr.doctype.interview.interview.send_interview_confirmation",
							args: { interview: r.message },
							callback(res) {
								if (!res.exc) {
									frappe.show_alert({
										message: __("Interview scheduled and confirmation sent"),
										indicator: "green",
									});
								}
							},
						});
					} else {
						frappe.show_alert({
							message: __("Interview scheduled successfully"),
							indicator: "green",
						});
					}
					d.hide();
					frm.events.get_interview_for_dashboard(frm);
				}
			},
		});
	},
});
