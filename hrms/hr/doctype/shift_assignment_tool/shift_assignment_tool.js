// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shift Assignment Tool", {
	setup(frm) {
		hrms.setup_employee_filter_group(frm);
	},

	get_employees(frm) {
		if (!frm.doc.from_date)
			return frm.events.render_employees_datatable(frm, []);

		frm
			.call({
				method: "get_employees",
				args: {
					advanced_filters: frm.advanced_filters || [],
				},
				doc: frm.doc,
			})
			.then((r) => frm.events.render_employees_datatable(frm, r.message));
	},
});
