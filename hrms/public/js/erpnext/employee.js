// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee", {
	refresh: function (frm) {
		frm.set_query("payroll_cost_center", function () {
			return {
				filters: {
					company: frm.doc.company,
					is_group: 0,
				},
			};
		});

		// filter advance account based on salary currency
		if (frm.doc.salary_currency) {
			frm.set_query("employee_advance_account", function () {
				return {
					filters: {
						root_type: "Asset",
						is_group: 0,
						company: frm.doc.company,
						account_currency: frm.doc.salary_currency,
						account_type: "Receivable",
					},
				};
			});
		}
		frm.set_df_property("holiday_list", "hidden", 1);

		// hide naming series field based on hr settings
		frappe.db.get_single_value("HR Settings", "emp_created_by").then((value) => {
			frm.toggle_display("naming_series", value === "Naming Series");
		});

		frm.trigger("add_assignment_actions");
	},

	add_assignment_actions: async function (frm) {
		if (frm.is_new() || frm.doc.status !== "Active") return;

		const { get_assignment_actions, get_assignable_masters, open_assignment } =
			hrms.assignments;
		const available_masters = await get_assignable_masters(frm.doc.company);
		const ctx = {
			employee: frm.doc.name,
			employee_name: frm.doc.employee_name,
			company: frm.doc.company,
			date_of_joining: frm.doc.date_of_joining,
		};

		for (const action of get_assignment_actions()) {
			if (action.master && !available_masters[action.master]) continue;
			if (!frappe.model.can_create(action.doctype)) continue;

			frm.add_custom_button(
				action.label,
				() => open_assignment(ctx, action),
				__("Create Assignments"),
			);
		}
	},

	date_of_birth(frm) {
		frm.call({
			method: "hrms.overrides.employee_master.get_retirement_date",
			args: {
				date_of_birth: frm.doc.date_of_birth,
			},
		}).then((r) => {
			if (r && r.message) frm.set_value("date_of_retirement", r.message);
		});
	},
});

// The profile is a page of its own, as on /employee-profile: its card replaces the side panel, and
// with no comments below it, the card stays pinned to the end. Both show on the other tabs.
frappe.ui.form.on("Employee", {
	refresh: toggle_form_panels,
	on_tab_change: toggle_form_panels,
});

function toggle_form_panels(frm) {
	const tab = frm.get_active_tab() || frm.layout.tabs.find((tab) => !tab.is_hidden());
	const on_profile = !frm.is_new() && tab?.df.fieldname === "profile";
	frm.page.sidebar.toggleClass("hidden", on_profile);
	frm.footer?.wrapper.toggleClass("hidden", on_profile);
}
