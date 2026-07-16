// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Holiday List", {
	refresh: function (frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(
			__("Holiday List Assignment"),
			function () {
				const doc = frappe.model.get_new_doc("Holiday List Assignment");
				doc.holiday_list = frm.doc.name;
				doc.from_date = frm.doc.from_date;
				frappe.set_route("Form", "Holiday List Assignment", doc.name);
			},
			__("Create"),
		);
	},
});
