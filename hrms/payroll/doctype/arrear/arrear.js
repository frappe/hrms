// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Arrear", {
	setup(frm) {
		const companyFilter = () =>
			frm.doc.company ? { filters: { company: frm.doc.company } } : {};
		frm.set_query("employee", () => companyFilter());
		frm.set_query("payroll_period", () => companyFilter());
		frm.set_query("salary_structure", () => companyFilter());
	},

	employee: (frm) => {
		if (frm.doc.employee) {
			frm.trigger("get_employee_currency");
			frm.trigger("set_company");
		} else {
			frm.set_value("company", null);
		}
	},

	get_employee_currency: (frm) => {
		frappe.call({
			method: "hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment.get_employee_currency",
			args: {
				employee: frm.doc.employee,
			},
			callback: (r) => {
				if (r.message) {
					frm.set_value("currency", r.message);
				}
			},
		});
	},

	set_company: (frm) => {
		if (frm.doc.employee) {
			return frappe.db
				.get_value("Employee", frm.doc.employee, "company")
				.then(({ message }) => {
					if (message?.company) {
						frm.set_value("company", message.company);
					}
				});
		}
	},
});
