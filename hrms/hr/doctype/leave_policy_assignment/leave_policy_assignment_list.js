frappe.listview_settings['Leave Policy Assignment'] = {
	onload: function (list_view) {
		list_view.page.add_inner_button(__("Bulk Leave Policy Assignment"), function () {
			frappe.set_route("Form", "Leave Control Panel")
		});
	},
};
