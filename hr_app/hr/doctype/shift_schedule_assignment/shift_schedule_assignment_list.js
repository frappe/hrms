frappe.listview_settings["Shift Schedule Assignment"] = {
	onload: (list_view) => hrms.add_shift_tools_button_to_list(list_view, "Assign Shift Schedule"),
};
