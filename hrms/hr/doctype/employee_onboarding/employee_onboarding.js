// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Onboarding", {
	setup: function (frm) {
		frm.set_query("job_offer", function () {
			return {
				filters: {
					status: "Accepted",
					docstatus: 1,
				},
			};
		});
	},

	onload_post_render: function (frm) {
		frappe.require("employee_onboarding_checklist.bundle.js", () => {
			frm.trigger("render_checklist");
		});
	},

	refresh: function (frm) {
		if (frm.doc.employee) {
			frm.add_custom_button(
				__("Employee"),
				function () {
					frappe.set_route("Form", "Employee", frm.doc.employee);
				},
				__("View"),
			);
		}

		frm.trigger("sync_appointment_letter");
		frm.trigger("render_checklist");
	},

	sync_appointment_letter: function (frm) {
		if (frm.is_new() || frm.doc.appointment_letter) return;

		frm.call({ method: "sync_appointment_letter", doc: frm.doc }).then((r) => {
			if (r.message) frm.refresh();
		});
	},

	render_checklist: function (frm) {
		if (!hrms.ui?.EmployeeOnboardingChecklist) return;

		frm._onboarding_checklist ??= new hrms.ui.EmployeeOnboardingChecklist({ frm });
		frm._onboarding_checklist.render();
	},

	employee_onboarding_template: function (frm) {
		// Standard rows stay; only the previous template's own rows give way.
		frm.doc.activities = (frm.doc.activities || []).filter((row) => row.action !== "Manual");
		refresh_field("activities");
		frm.trigger("render_checklist");
		if (!frm.doc.employee_onboarding_template) return;

		frappe.call({
			method: "hrms.controllers.employee_boarding_controller.get_onboarding_details",
			args: {
				parent: frm.doc.employee_onboarding_template,
				parenttype: "Employee Onboarding Template",
			},
			callback: function (r) {
				if (!r.message) return;
				r.message.forEach((d) => frm.add_child("activities", { ...d, action: "Manual" }));
				refresh_field("activities");
				frm.trigger("render_checklist");
			},
		});

		if (frm.doc.documents?.length) return;

		frappe.db
			.get_doc("Employee Onboarding Template", frm.doc.employee_onboarding_template)
			.then((template) => {
				(template.required_documents || []).forEach((row) =>
					frm.add_child("documents", {
						document_name: row.document_name,
						required: row.required,
						description: row.description,
					}),
				);
				refresh_field("documents");
			});
	},

	job_applicant: function (frm) {
		frm.trigger("render_checklist");
	},

	job_offer: function (frm) {
		if (!frm.doc.job_offer) {
			frm.set_value("employee", "");
			return;
		}
		frappe.db.get_value("Employee", { job_offer: frm.doc.job_offer }, "name", (r) => {
			frm.set_value("employee", r && r.name ? r.name : "");
		});
	},
});
