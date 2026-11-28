// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Referral", {
	refresh: function (frm) {
		if (frm.doc.docstatus === 1 && frm.doc.status === "Pending") {
			frm.add_custom_button(__("Reject Employee Referral"), function () {
				frappe.confirm(
					__("Reject the referral for {0}?", [frm.doc.full_name]),
					function () {
						frm.events.reject_referral(frm);
					},
				);
			});

			frm.add_custom_button(
				__("Create Job Applicant"),
				function () {
					frm.events.create_job_applicant(frm);
				},
				null,
				"primary",
			);
		}

		// To check whether Payment is done or not
		if (frm.doc.docstatus === 1 && frm.doc.status === "Accepted") {
			frappe.db
				.get_list("Additional Salary", {
					filters: {
						ref_docname: cur_frm.doc.name,
						docstatus: 1,
					},
					fields: [{ COUNT: "name", as: "additional_salary_count" }],
				})
				.then((data) => {
					let additional_salary_count = data[0].additional_salary_count;

					if (frm.doc.is_applicable_for_referral_bonus && !additional_salary_count) {
						frm.add_custom_button(
							__("Create Additional Salary"),
							function () {
								frm.events.create_additional_salary(frm);
							},
							null,
							"primary",
						);
					}
				});
		}
	},
	create_job_applicant: function (frm) {
		frappe
			.call({
				method: "hrms.hr.doctype.employee_referral.employee_referral.create_job_applicant",
				args: {
					source_name: frm.docname,
				},
			})
			.then(() => frm.reload_doc());
	},

	reject_referral: function (frm) {
		frappe
			.call({
				method: "hrms.hr.doctype.employee_referral.employee_referral.reject_referral",
				args: {
					source_name: frm.docname,
				},
			})
			.then(() => frm.reload_doc());
	},

	create_additional_salary: function (frm) {
		frappe.call({
			method: "hrms.hr.doctype.employee_referral.employee_referral.create_additional_salary",
			args: {
				employee_referral: frm.doc.name,
			},
			callback: function (r) {
				var doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			},
		});
	},
});
