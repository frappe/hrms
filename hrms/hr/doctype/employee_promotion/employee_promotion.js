// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

{% include 'hrms/hr/employee_property_update.js' %}

frappe.ui.form.on("Employee Promotion", {
	setup: function (frm) {
		frm.set_query("salary_structure", function () {
			return {
				filters: {
					company: frm.doc.company,
					docstatus: 1,
					is_active: "Yes",
				},
			};
		});
	},

	refresh: function (frm) {
		frm.revised_ctc_is_calculated = Boolean(frm.doc.salary_structure && frm.doc.revised_base);
		frm.trigger("show_assignment_hint");

		const { docstatus, salary_structure, revised_base } = frm.doc;
		if (
			docstatus !== 1 ||
			!salary_structure ||
			!revised_base ||
			frm.doc.revised_salary_structure_assignment ||
			!frappe.model.can_create("Salary Structure Assignment")
		)
			return;

		frm.add_custom_button(__("Create Salary Structure Assignment"), () => {
			frappe.model.open_mapped_doc({
				method: "hrms.hr.doctype.employee_promotion.employee_promotion.make_salary_structure_assignment",
				frm: frm,
			});
		});
	},

	show_assignment_hint: function (frm) {
		frm.set_intro("");
		const {
			docstatus,
			salary_structure,
			revised_base,
			revised_salary_structure_assignment: assignment,
		} = frm.doc;

		// a saved draft already gets Frappe's "Submit this document to confirm"
		if (
			frm.is_new() &&
			salary_structure &&
			revised_base &&
			frappe.model.can_create("Salary Structure Assignment")
		) {
			frm.set_intro(__("Submit this promotion to create its Salary Structure Assignment."), "blue");
		} else if (docstatus === 1 && assignment && frm.doc.__onload?.assignment_is_draft) {
			frm.set_intro(
				__("Salary Structure Assignment {0} is a draft. Submit it so payroll uses the revised salary.", [
					frappe.utils.get_form_link("Salary Structure Assignment", assignment, true),
				]),
				"yellow",
			);
		}
	},

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
		frm.trigger("show_assignment_hint");
	},

	revised_base: function (frm) {
		frm.trigger("set_revised_ctc");
		frm.trigger("show_assignment_hint");
	},

	set_revised_ctc: function (frm) {
		if (!frm.doc.salary_structure || !frm.doc.revised_base) {
			// clear only a calculated CTC; one typed by hand stays
			if (frm.revised_ctc_is_calculated) {
				frm.revised_ctc_is_calculated = false;
				frm.set_value("revised_ctc", null);
			}
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
				frm.revised_ctc_is_calculated = true;
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
		current_salary_structure: assignment.salary_structure || "",
		salary_structure: assignment.salary_structure || "",
		current_base: assignment.base || 0,
		current_ctc: assignment.ctc || 0,
	});
}
