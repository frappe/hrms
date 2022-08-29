// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Hiring Request", {
	refresh: function(frm) {
		if (frm.doc.status === "Open & Approved") {
			frm.add_custom_button(__("Create Job Opening"), () => {
				frappe.model.open_mapped_doc({
					method: "hrms.hr.doctype.hiring_request.hiring_request.make_job_opening",
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
						return {
							filters: {
								"company": frm.doc.company,
								"status": "Open",
								"staffing_plan": ("is", "Not Set")
							}
						};
					}
				}, (values) => {
					frm.call("associate_job_opening", {job_opening: values.job_opening});
				}, __("Associate Job Opening"), __("Submit"));
			}, __("Actions"));

			frm.page.set_inner_btn_group_as_primary(__("Actions"));
		}
	}
});
