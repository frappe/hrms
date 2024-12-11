frappe.listview_settings["Shift Assignment"] = {
	onload: function (list_view) {
		list_view.page.add_inner_button(
			__("Shift Assignment Tool"),
			function () {
				frappe.set_route("Form", "Shift Assignment Tool");
			},
			__("View"),
		);

		list_view.page.add_inner_button(
			__("Roster"),
			function () {
				window.location.href = "/hr/roster";
			},
			__("View"),
		);
	},
};
