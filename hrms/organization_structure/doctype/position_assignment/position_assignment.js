// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Position Assignment", {
	position(frm) {
		if (!frm.doc.position) return;

		frappe.db.get_value("Position", frm.doc.position, ["is_occupied", "current_employee"]).then((r) => {
			const data = r.message;
			if (data && data.is_occupied && data.current_employee !== frm.doc.employee) {
				frappe.msgprint({
					title: __("Position Occupied"),
					message: __("This position is currently occupied by {0}.", [
						data.current_employee.bold(),
					]),
					indicator: "orange",
				});
			}
		});
	},
});
