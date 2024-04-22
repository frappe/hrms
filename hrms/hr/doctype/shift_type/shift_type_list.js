frappe.listview_settings["Shift Type"] = {
	onload: function (list_view) {
		list_view.page.add_inner_button(__("Shift Assignment Tool"), function () {
			frappe.set_route("Form", "Shift Assignment Tool");
		});
	},
};
