// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Income Tax Slab", {
	refresh: function (frm) {
		if (frm.doc.docstatus != 1) return;
		frm.add_custom_button(
			__("Salary Structure Assignment"),
			() => {
				frappe.model.with_doctype("Salary Structure Assignment", () => {
					const doc = frappe.model.get_new_doc("Salary Structure Assignment");
					doc.income_tax_slab = frm.doc.name;
					frappe.set_route("Form", "Salary Structure Assignment", doc.name);
				});
			},
			__("Create"),
		);
		frm.page.set_inner_btn_group_as_primary(__("Create"));
	},

	currency: function (frm) {
		frm.refresh_fields();
	},
});
