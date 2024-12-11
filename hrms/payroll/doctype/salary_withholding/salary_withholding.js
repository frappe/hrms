// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Salary Withholding", {
	employee(frm) {
		if (!frm.doc.employee) return;

		frappe
			.call({
				method: "hrms.payroll.doctype.salary_withholding.salary_withholding.get_payroll_frequency",
				args: {
					employee: frm.doc.employee,
					posting_date: frm.doc.posting_date,
				},
			})
			.then((r) => {
				if (r.message) {
					frm.set_value("payroll_frequency", r.message);
				}
			});
	},

	from_date(frm) {
		if (!frm.doc.from_date || !frm.doc.payroll_frequency)
			frappe.msgprint(__("Please select From Date and Payroll Frequency first"));

		frm.call({
			method: "set_withholding_cycles_and_to_date",
			doc: frm.doc,
		}).then((r) => {
			frm.refresh_field("to_date");
			frm.refresh_field("cycles");
		});
	},
});
