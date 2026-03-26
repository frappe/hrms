// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Holiday List Assignment", {
	refresh: function (frm) {
		frm.trigger("switch_assigned_to_label");
	},
	applicable_for: function (frm) {
		frm.trigger("toggle_fields");
		frm.trigger("clear_fields");
		frm.trigger("switch_assigned_to_label");
	},
	toggle_fields: function (frm) {
		frm.toggle_display(
			["employee_name", "employee_company"],
			frm.doc.applicable_for == "Employee",
		);
	},
	clear_fields: function (frm) {
		frm.set_value("assigned_to", "");
		frm.set_value("employee_name", "");
		frm.set_value("employee_company", "");
	},
	assigned_to: function (frm) {
		if (frm.doc.applicable_for == "Employee" && frm.doc.assigned_to) {
			frm.trigger("toggle_fields");
			frappe.db.get_value(
				"Employee",
				frm.doc.assigned_to,
				["employee_name", "company"],
				(r) => {
					frm.set_value("employee_name", r.employee_name);
					frm.set_value("employee_company", r.company);
				},
			);
		}
	},
	holiday_list: function (frm) {
		frm.trigger("set_start_and_end_dates");
	},
	set_start_and_end_dates: function (frm) {
		if (!frm.doc.holiday_list) return;
		frappe.db.get_value(
			"Holiday List",
			frm.doc.holiday_list,
			["from_date", "to_date"],
			(r) => {
				frm.set_value("from_date", r.from_date);
				frm.set_value("holiday_list_start", r.from_date);
				frm.set_value("holiday_list_end", r.to_date);
			},
		);
	},
	switch_assigned_to_label: function (frm) {
		frm.set_df_property("assigned_to", "label", frm.doc.applicable_for);
	},
});
