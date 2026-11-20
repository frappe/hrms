// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Job Requisition", {
	refresh: function (frm) {
		if (!frm.doc.__islocal && !["Filled", "On Hold", "Cancelled"].includes(frm.doc.status)) {
			frappe.db
				.get_list("Employee Referral", {
					filters: { for_designation: frm.doc.designation, status: "Pending" },
				})
				.then((data) => {
					if (data && data.length) {
						const link =
							data.length > 1
								? `<a id="referral_links" style="text-decoration: underline;">${__(
										"Employee Referrals",
								  )}</a>`
								: `<a id="referral_links" style="text-decoration: underline;">${__(
										"Employee Referral",
								  )}</a>`;

						const headline = __("{} {} open for this position.", [data.length, link]);
						frm.dashboard.clear_headline();
						frm.dashboard.set_headline(headline, "yellow");

						$("#referral_links").on("click", (e) => {
							e.preventDefault();
							frappe.set_route("List", "Employee Referral", {
								for_designation: frm.doc.designation,
								status: "Pending",
							});
						});
					}
				});
		}

		if (frm.doc.status === "Open & Approved") {
			frm.trigger("add_job_opening_buttons");
		}

		frm.trigger("set_text_heights");
	},

	set_text_heights: function (frm) {
		frm.fields_dict.description.$wrapper.find(".ql-editor").css("height", "160px");
		frm.fields_dict.reason_for_requesting.$input?.css("height", "80px");
	},

	add_job_opening_buttons: async function (frm) {
		const openings = await frappe.db.get_list("Job Opening", {
			filters: { job_requisition: frm.doc.name },
			pluck: "name",
		});

		if (openings.length) {
			frm.add_custom_button(__("View job opening"), () => {
				if (openings.length === 1) {
					frappe.set_route("Form", "Job Opening", openings[0]);
				} else {
					frappe.set_route("List", "Job Opening", { job_requisition: frm.doc.name });
				}
			});
		} else {
			frm.add_custom_button(
				__("Create Job Opening"),
				() => {
					frappe.model.open_mapped_doc({
						method: "hrms.hr.doctype.job_requisition.job_requisition.make_job_opening",
						frm: frm,
					});
				},
				__("Actions"),
			);
		}

		frm.add_custom_button(
			__("Associate Job Opening"),
			() => {
				frappe.prompt(
					{
						label: __("Job Opening"),
						fieldname: "job_opening",
						fieldtype: "Link",
						options: "Job Opening",
						reqd: 1,
						get_query: () => {
							const filters = {
								company: frm.doc.company,
								status: "Open",
								designation: frm.doc.designation,
							};

							if (frm.doc.department) filters.department = frm.doc.department;

							return { filters: filters };
						},
					},
					(values) => {
						frm.call("associate_job_opening", { job_opening: values.job_opening });
					},
					__("Associate Job Opening"),
					__("Submit"),
				);
			},
			__("Actions"),
		);

		if (!openings.length) frm.page.set_inner_btn_group_as_primary(__("Actions"));
	},
	before_save: function (frm) {
		frm.trigger("handle_duplicate_check");
	},
	handle_duplicate_check: function (frm) {
		if (!frm.is_new() || frm.duplicate_confirmed) return;
		frappe.validated = false;

		frm.call("check_duplicate_job_requisition").then((r) => {
			if (!r.message) {
				frm.duplicate_confirmed = true;
				frm.save();
				return;
			}

			frappe.confirm(
				__(
					"A Job Requisition already exists for {0} requested by {1} for the same department.<br> Do you want to continue?",
					[frm.doc.designation.bold(), frm.doc.requested_by.bold()],
				),
				() => {
					frm.duplicate_confirmed = true;
					frm.save();
				},
			);
		});
	},
});
