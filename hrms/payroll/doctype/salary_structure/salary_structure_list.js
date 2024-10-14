frappe.listview_settings["Salary Structure"] = {
	onload: function (list_view) {
		list_view.page.add_inner_button(__("Bulk Salary Structure Assignment"), function () {
			frappe.set_route("Form", "Bulk Salary Structure Assignment");
		});
	},
};
