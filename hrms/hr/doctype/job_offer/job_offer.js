// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide("erpnext.job_offer");

frappe.ui.form.on("Job Offer", {
	onload: function (frm) {
		frm.set_query("select_terms", function () {
			return { filters: { hr: 1 } };
		});
	},

	setup: function (frm) {
		frm.email_field = "applicant_email";
	},

	select_terms: function (frm) {
		erpnext.utils.get_terms(frm.doc.select_terms, frm.doc, function (r) {
			if (!r.exc) {
				frm.set_value("terms", r.message);
			}
		});
	},
	job_offer_term_template: function (frm) {
		if (!frm.doc.job_offer_term_template) return;

		frappe.db
			.get_doc("Job Offer Term Template", frm.doc.job_offer_term_template)
			.then((doc) => {
				frm.clear_table("offer_terms");
				doc.offer_terms.forEach((term) => {
					frm.add_child("offer_terms", term);
				});
				refresh_field("offer_terms");
			});
	},

	refresh: function (frm) {
		if (
			!frm.doc.__islocal &&
			frm.doc.status == "Accepted" &&
			frm.doc.docstatus === 1 &&
			(!frm.doc.__onload || !frm.doc.__onload.employee)
		) {
			frm.add_custom_button(__("Create Employee"), function () {
				erpnext.job_offer.make_employee(frm);
			});
		}

		if (frm.doc.__onload && frm.doc.__onload.employee) {
			frm.add_custom_button(__("Show Employee"), function () {
				frappe.set_route("Form", "Employee", frm.doc.__onload.employee);
			});
		}

		if (frm.doc.docstatus === 1 && frm.doc.status !== "Cancelled" && frm.doc.applicant_email) {
			const offer_sent = frm.doc.__onload && frm.doc.__onload.offer_letter_sent;
			frm.add_custom_button(
				offer_sent ? __("Resend Offer Letter") : __("Send Offer Letter"),
				() => {
					frappe.db
						.get_single_value("HR Settings", "hiring_sender_email")
						.then((sender) => {
							if (!sender) {
								frappe.msgprint({
									title: __("Sender Email Not Configured"),
									message: __(
										"Please set {0} in {1} before sending offer letters.",
										[
											`<b>${__("Hiring Sender Email")}</b>`,
											`<a href="/desk/hr-settings/HR%20Settings#recruitment_tab" target="_blank">${__(
												"HR Settings",
											)}</a>`,
										],
									),
									indicator: "orange",
								});
								return;
							}
							frm.events.show_send_offer_dialog(frm, offer_sent);
						});
				},
			);
		}
	},
	show_send_offer_dialog: function (frm, is_resend) {
		const dialog = new frappe.ui.Dialog({
			title: is_resend ? __("Resend Offer Letter") : __("Send Offer Letter"),
			fields: [
				{
					fieldtype: "HTML",
					options: `<p>${__(
						"An offer letter will be sent to {0}. The Job Offer will be attached as a PDF.",
						[`<b>${frm.doc.applicant_email}</b>`],
					)}</p>`,
				},
				{
					label: __("Email Template"),
					fieldname: "email_template",
					fieldtype: "Link",
					options: "Email Template",
					description: __(
						"Optional. Leave blank to use the default template. Create your own via {0}.",
						[
							`<a href="/desk/email-template" target="_blank">${__(
								"Email Template",
							)}</a>`,
						],
					),
				},
				{
					label: __("Print Format"),
					fieldname: "print_format",
					fieldtype: "Link",
					options: "Print Format",
					default: frm.meta.default_print_format || "",
					get_query: () => ({ filters: { doc_type: "Job Offer" } }),
					description: __("The selected print format will be attached as PDF."),
				},
			],
			primary_action_label: __("Send"),
			primary_action(values) {
				const print_format = values.print_format || frm.meta.default_print_format || "";
				dialog.get_primary_btn().prop("disabled", true).text(__("Sending..."));
				frappe.call({
					method: "hrms.hr.doctype.job_offer.job_offer.send_offer_letter",
					args: {
						job_offer: frm.doc.name,
						email_template: values.email_template || null,
						print_format: print_format || null,
					},
					callback(r) {
						if (!r.exc) {
							dialog.hide();
							frm.reload_doc();
							frappe.show_alert({
								message: __("Offer letter sent to {0}", [frm.doc.applicant_email]),
								indicator: "green",
							});
						} else {
							dialog.get_primary_btn().prop("disabled", false).text(__("Send"));
						}
					},
				});
			},
			secondary_action_label: __("Preview"),
			secondary_action() {
				const values = dialog.get_values(true);
				const print_format = values.print_format || frm.meta.default_print_format || "";
				const format_param = print_format
					? `&format=${encodeURIComponent(print_format)}`
					: "";
				const preview_url = `/printview?doctype=Job+Offer&name=${encodeURIComponent(
					frm.doc.name,
				)}${format_param}`;
				window.open(preview_url, "_blank", "noopener");
			},
		});
		dialog.show();
	},
});

erpnext.job_offer.make_employee = function (frm) {
	frappe.model.open_mapped_doc({
		method: "hrms.hr.doctype.job_offer.job_offer.make_employee",
		frm: frm,
	});
};
