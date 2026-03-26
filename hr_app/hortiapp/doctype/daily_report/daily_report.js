frappe.ui.form.on("Daily Report", {
	refresh(frm) {
		if (frm.is_new() && !frm.doc.employee) {
			frappe.call({
				method: "hr_app.api.get_current_employee_info",
				callback(r) {
					if (r.message && r.message.name) {
						frm.set_value("employee", r.message.name);
					}
				},
			});
		}
	},
});
