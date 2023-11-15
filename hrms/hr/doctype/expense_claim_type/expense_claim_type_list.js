// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.listview_settings["Expense Claim Type"] = {
	onload(listview) {
		listview.page.add_inner_button(__("Expense Claims"), function () {
			frappe.set_route("List", "Expense Claim", {"expense_type": listview.get_filter_value("name")});
		});
	}
};
