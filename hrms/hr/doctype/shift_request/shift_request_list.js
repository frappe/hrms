frappe.listview_settings["Shift Request"] = {
	onload: function (list_view) {
		list_view.page.add_inner_button(__("Shift Assignment Tool"), function () {
			const doc = frappe.model.get_new_doc("Shift Assignment Tool");
			doc.action = "Process Shift Requests";
			frappe.set_route("Form", "Shift Assignment Tool", doc.name);
		});
	},
};
