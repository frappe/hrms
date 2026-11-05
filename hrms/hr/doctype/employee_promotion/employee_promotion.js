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

	employee_property_added: function (frm) {
		const row = (frm.doc.promotion_details || []).at(-1);
		if (!row || row.fieldname !== "grade" || !row.new) return;

		frappe.db
			.get_value("Employee Grade", row.new, ["default_salary_structure", "default_base_pay"])
			.then((r) => {
				const grade = r.message || {};
				const values = {};
				if (grade.default_salary_structure && grade.default_salary_structure !== frm.doc.salary_structure) {
					values.salary_structure = grade.default_salary_structure;
				}
				if (grade.default_base_pay && !frm.doc.revised_base) {
					values.revised_base = grade.default_base_pay;
				}
				frm.set_value(values);
			});
	},

	salary_structure: function (frm) {
		frm.trigger("set_revised_ctc");
	},

	revised_base: function (frm) {
		frm.trigger("set_revised_ctc");
	},

	set_revised_ctc: function (frm) {
		if (!frm.doc.salary_structure) return;
		if (!frm.doc.revised_base) {
			frm.set_value("revised_ctc", 0);
			return;
		}

		const sent = revised_ctc_inputs(frm);
		frappe
			.call({
				method: "hrms.hr.doctype.employee_promotion.employee_promotion.calculate_revised_ctc",
				args: { promotion: frm.doc },
			})
			.then((r) => {
				if (revised_ctc_inputs(frm) !== sent) return;
				frm.set_value("revised_ctc", r.message || 0);
			});
	},
});

function revised_ctc_inputs(frm) {
	const { employee, promotion_date, salary_structure, revised_base } = frm.doc;
	return JSON.stringify([employee, promotion_date, salary_structure, revised_base]);
}

function set_salary_fields(frm, assignment) {
	frm.set_value({
		current_salary_structure_assignment: assignment.name || "",
		salary_structure: assignment.salary_structure || "",
		current_base: assignment.base || 0,
		current_ctc: assignment.ctc || 0,
	});
}
