frappe.listview_settings['Leave Policy Assignment'] = {
	onload: function (list_view) {
		list_view.page.add_inner_button(__("Bulk Leave Policy Assignment"), function () {
			frappe.set_route("leave-control-panel")
		});
	},

	set_effective_date: function () {
		if (cur_dialog.fields_dict.assignment_based_on.value === "Leave Period" && cur_dialog.fields_dict.leave_period.value) {
			frappe.model.with_doc("Leave Period", cur_dialog.fields_dict.leave_period.value, function () {
				let from_date = frappe.model.get_value("Leave Period", cur_dialog.fields_dict.leave_period.value, "from_date");
				let to_date = frappe.model.get_value("Leave Period", cur_dialog.fields_dict.leave_period.value, "to_date");
				cur_dialog.set_value("effective_from", from_date);
				cur_dialog.set_value("effective_to", to_date);
			});
		}
	}
};
