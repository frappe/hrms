// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Job Requisition", {
	refresh: function(frm) {
		if (!frm.doc.__islocal && !["Filled", "On Hold", "Cancelled"].includes(frm.doc.status)) {
			frappe.db.get_list("Employee Referral", {
				filters: { for_designation: frm.doc.designation, status: "Pending" }
			}).then((data) => {
				if (data && data.length) {
					const link = data.length > 1
						? `<a id="referral_links" style="text-decoration: underline;">${__("Employee Referrals")}</a>`
						: `<a id="referral_links" style="text-decoration: underline;">${__("Employee Referral")}</a>`;

					const headline = __("{} {} open for this position.", [data.length, link]);
					frm.dashboard.clear_headline();
					frm.dashboard.set_headline(headline, "yellow");

					$("#referral_links").on("click", (e) => {
						e.preventDefault();
						frappe.set_route("List", "Employee Referral", {
							for_designation: frm.doc.designation,
							status: "Pending"
						});
					});
				}
			})
		}

		if (frm.doc.status === "Open & Approved") {
			frm.add_custom_button(__("Create Job Opening"), () => {
				frappe.model.open_mapped_doc({
					method: "hrms.hr.doctype.job_requisition.job_requisition.make_job_opening",
					frm: frm
				});
			}, __("Actions"));

			frm.add_custom_button(__("Associate Job Opening"), () => {
				frappe.prompt({
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
						}

						if (frm.doc.department)
							filters.department = frm.doc.department;

						return { filters: filters };
					}
				}, (values) => {
					frm.call("associate_job_opening", { job_opening: values.job_opening });
				}, __("Associate Job Opening"), __("Submit"));
			}, __("Actions"));

			frm.page.set_inner_btn_group_as_primary(__("Actions"));
		}
	}
});
