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
		frappe.require("employee_onboarding_wizard.bundle.js", () => {
			frm.trigger("render_wizard");
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
		frm.trigger("render_wizard");
	},

	sync_appointment_letter: function (frm) {
		if (frm.is_new() || frm.doc.appointment_letter) return;

		frm.call({ method: "sync_appointment_letter", doc: frm.doc }).then((r) => {
			if (r.message) frm.refresh();
		});
	},

	render_wizard: function (frm) {
		if (!hrms.ui?.EmployeeOnboardingWizard || !frm.page?.main?.length) return;

		const $main = frm.page.main;
		$main.addClass("employee-onboarding-custom-page flex flex-col flex-1");

		let $mount = $main.find(".employee-onboarding-wizard-root");
		if (!$mount.length) {
			$mount = $(
				'<div class="employee-onboarding-wizard-root flex flex-1 w-full min-h-0"></div>',
			).prependTo($main);
		}

		try {
			if (frm._onboarding_wizard?.frm === frm) {
				frm._onboarding_wizard.refresh_from_frm();
			} else {
				frm._onboarding_wizard?.unmount?.();
				frm._onboarding_wizard = new hrms.ui.EmployeeOnboardingWizard({
					wrapper: $mount[0],
					frm,
				});
			}
			frm.layout?.wrapper?.hide();
		} catch (error) {
			console.error("Employee Onboarding wizard mount failed", error);
			frm._onboarding_wizard = null;
			$mount.remove();
			frm.layout?.wrapper?.show();
			frappe.show_alert({
				message: __("Could not load the onboarding wizard. Please refresh the page."),
				indicator: "red",
			});
		}
	},

	employee_onboarding_template: function (frm) {
		frm.set_value("activities", "");
		if (!frm.doc.employee_onboarding_template) return;

		frappe.call({
			method: "hrms.controllers.employee_boarding_controller.get_onboarding_details",
			args: {
				parent: frm.doc.employee_onboarding_template,
				parenttype: "Employee Onboarding Template",
			},
			callback: function (r) {
				if (!r.message) return;
				r.message.forEach((d) => frm.add_child("activities", d));
				refresh_field("activities");
				frm._onboarding_wizard?.refresh_from_frm();
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
				frm._onboarding_wizard?.refresh_from_frm();
			});
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
