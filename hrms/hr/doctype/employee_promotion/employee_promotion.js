// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

{% include 'hrms/hr/employee_property_update.js' %}

frappe.ui.form.on("Employee Promotion", {
	employee: function (frm) {
		frm.trigger("set_current_salary");
	},

	promotion_date: function (frm) {
		frm.trigger("set_current_salary");
	},

	set_current_salary: function (frm) {
		const { employee, promotion_date } = frm.doc;
		if (!employee || !promotion_date) {
			set_salary_fields(frm, {});
			return;
		}

		frappe
			.call({
				method: "hrms.hr.doctype.employee_promotion.employee_promotion.get_current_salary",
				args: { employee, on_date: promotion_date },
			})
			.then((r) => {
				if (frm.doc.employee !== employee || frm.doc.promotion_date !== promotion_date) return;
				set_salary_fields(frm, r.message || {});
			});
	},
});

function set_salary_fields(frm, assignment) {
	frm.set_value({
		current_salary_structure_assignment: assignment.name || "",
		salary_structure: assignment.salary_structure || "",
		current_base: assignment.base || 0,
		current_ctc: assignment.ctc || 0,
	});
}
