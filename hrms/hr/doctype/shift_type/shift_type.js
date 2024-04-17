// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shift Type", {
	refresh: function (frm) {
		if (frm.doc.__islocal) return;

		frm.add_custom_button(
			__("Bulk Assign Shift"),
			() => {
				const doc = frappe.model.get_new_doc("Shift Assignment Tool");
				doc.action = "Assign Shift";
				doc.company = frappe.defaults.get_default("company");
				doc.shift_type = frm.doc.name;
				doc.status = "Active";
				frappe.set_route("Form", "Shift Assignment Tool", doc.name);
			},
			__("Actions"),
		);

		frm.add_custom_button(
			__("Mark Attendance"),
			() => {
				if (!frm.doc.enable_auto_attendance) {
					frm.scroll_to_field("enable_auto_attendance");
					frappe.throw(
						__("Please Enable Auto Attendance and complete the setup first."),
					);
				}

				if (!frm.doc.process_attendance_after) {
					frm.scroll_to_field("process_attendance_after");
					frappe.throw(__("Please set {0}.", [__("Process Attendance After").bold()]));
				}

				if (!frm.doc.last_sync_of_checkin) {
					frm.scroll_to_field("last_sync_of_checkin");
					frappe.throw(__("Please set {0}.", [__("Last Sync of Checkin").bold()]));
				}

				frm.call({
					doc: frm.doc,
					method: "process_auto_attendance",
					freeze: true,
					callback: () => {
						frappe.msgprint(
							__("Attendance has been marked as per employee check-ins"),
						);
					},
				});
			},
			__("Actions"),
		);
	},
});
