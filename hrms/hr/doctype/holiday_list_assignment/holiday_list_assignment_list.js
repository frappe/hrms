// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.listview_settings["Holiday List Assignment"] = {
	onload: (list_view) => {
		list_view.page.add_inner_button(__("Bulk Holiday Assignment"), () => {
			frappe.set_route("Form", "Bulk Holiday List Assignment");
		});
	},
};
