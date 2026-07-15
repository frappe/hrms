// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Leave Policy", {
	refresh: function (frm) {
		if (frm.doc.docstatus !== 1) return;

		frm.add_custom_button(
			__("Single Assignment"),
			function () {
				frappe.new_doc("Leave Policy Assignment", {
					leave_policy: frm.doc.name,
				});
			},
			__("Create"),
		);

		frm.add_custom_button(
			__("Bulk Assignment"),
			function () {
				frappe.model.with_doctype("Leave Control Panel", () => {
					const doc = frappe.model.get_new_doc("Leave Control Panel");
					doc.leave_policy = frm.doc.name;
					frappe.set_route("Form", "Leave Control Panel", doc.name);
				});
			},
			__("Create"),
		);

		frm.page.set_inner_btn_group_as_primary(__("Create"));
	},
});

frappe.ui.form.on("Leave Policy Detail", {
	leave_type: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.leave_type) {
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Leave Type",
					fieldname: "max_leaves_allowed",
					filters: { name: child.leave_type },
				},
				callback: function (r) {
					if (r.message) {
						child.annual_allocation = r.message.max_leaves_allowed;
						refresh_field("leave_policy_details");
					}
				},
			});
		} else {
			child.annual_allocation = "";
			refresh_field("leave_policy_details");
		}
	},
});
