// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Salary Withholding", {
	employee: function (frm) {
		if (!frm.doc.employee) {
			frm.set_value("employee_name", null);
			frm.set_value("payroll_frequency", null);
			frm.set_value("date_of_joining", null);
			frm.set_value("date_of_relieving", null);
			return;
		}

		frappe.call({
			method: "hrms.hr.doctype.salary_withholding.salary_withholding.get_employee_details",
			args: { employee: frm.doc.employee },
			callback: function (r) {
				frm.doc.date_of_joining = r.message.date_of_joining;
				frm.doc.date_of_relieving =
					r.message.relieving_date ||
					(r.message.resignation_letter_date &&
						frappe.datetime.add_months(
							r.message.resignation_letter_date,
							(months = r.message.notice_number_of_days),
						));
				frm.doc.employee_name = r.message.employee_name;
				frm.doc.payroll_frequency = r.message.payroll_frequency;

				frm.refresh_field("employee_name");
				frm.refresh_field("payroll_frequency");
				frm.refresh_field("date_of_joining");
				frm.refresh_field("date_of_relieving");
			},
		});
	},

	from_date: function (frm) {
		if (!frm.doc.from_date) return;
		if (!frm.doc.employee) {
			frappe.throw(__("Please select an employee"));
			frm.doc.from_date = null;
			frm.refresh_field("from_date");
		}
		if (!frm.doc.number_of_withholding_cycles) {
			frappe.throw(__("Please select number of withholding cycles"));
			frm.doc.from_date = null;
			frm.refresh_field("from_date");
		}

		frappe.call({
			method: "hrms.hr.doctype.salary_withholding.salary_withholding.get_salary_withholding_cycles_and_to_date",
			args: {
				payroll_frequency: frm.doc.payroll_frequency,
				from_date: frm.doc.from_date,
				number_of_withholding_cycles: frm.doc.number_of_withholding_cycles,
			},
			callback: function (r) {
				cycles = r.message.cycles;
				to_date = r.message.to_date;

				frm.doc.to_date = to_date;
				frm.doc.cycles = cycles.map((c) => {
					return {
						...c,
						salary_status: "Withheld",
					};
				});
				refresh_field("to_date");
				refresh_field("cycles");
			},
		});
	},
});
