// Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Appointment Letter Template", {
	onload: async function (frm) {
		if (!frm.is_new() || frm.doc.letter_body) return;
		const { message } = await frappe.call(
			"hrms.hr.doctype.appointment_letter_template.appointment_letter_template.get_default_letter_body",
		);
		frm.set_value("letter_body", message);
	},
});
