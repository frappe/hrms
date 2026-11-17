// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

{% include 'hrms/hr/employee_property_update.js' %}

frappe.ui.form.on("Employee Promotion", {
	setup: function (frm) {
		frm.email_field = "employee_email";

		frm.set_query("salary_structure", function () {
			return {
				filters: {
					company: frm.doc.company,
					docstatus: 1,
					is_active: "Yes",
				},
			};
		});

		frm.set_query("letter_print_format", function () {
			return { filters: { doc_type: "Employee Promotion", disabled: 0 } };
		});

		frm.set_query("select_terms", function () {
			return { filters: { hr: 1 } };
		});
	},

	select_terms: function (frm) {
		erpnext.utils.get_terms(frm.doc.select_terms, frm.doc, function (r) {
			if (!r.exc) {
				frm.set_value("terms", r.message);
			}
		});
	},

	refresh: function (frm) {
		frm.revised_ctc_is_calculated = Boolean(frm.doc.salary_structure && frm.doc.revised_base);
		frm.trigger("show_assignment_hint");
		render_revised_assignment(frm);
		add_assignment_button(frm);
		add_email_letter_button(frm);
		render_promotion_letter_preview(frm);
	},

	letter_print_format: function (frm) {
		render_promotion_letter_preview(frm);
	},

	letter_head: function (frm) {
		render_promotion_letter_preview(frm);
	},

	signature: function (frm) {
		render_promotion_letter_preview(frm);
	},

	terms: function (frm) {
		render_preview_after_typing(frm);
	},

	revised_ctc: function (frm) {
		render_promotion_letter_preview(frm);
	},

	on_tab_change: function (frm) {
		if (frm.get_active_tab()?.df?.fieldname === "promotion_letter_tab") {
			render_promotion_letter_preview(frm);
		}
	},

	show_assignment_hint: function (frm) {
		frm.set_intro("");
		const { docstatus, salary_structure, revised_base } = frm.doc;
		const assignment = get_revised_assignment(frm);

		// a saved draft already gets Frappe's "Submit this document to confirm"
		if (
			frm.is_new() &&
			salary_structure &&
			revised_base &&
			frappe.model.can_create("Salary Structure Assignment")
		) {
			frm.set_intro(__("Submit this promotion to create its Salary Structure Assignment."), "blue");
		} else if (docstatus === 1 && assignment?.docstatus === 0) {
			frm.set_intro(
				__("Salary Structure Assignment {0} is a draft. Submit it so payroll uses the revised salary.", [
					frappe.utils.get_form_link("Salary Structure Assignment", assignment.name, true),
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
			frm.trigger("set_revised_salary");
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
				// the revised salary depends on the employee, the date and the current assignment
				frm.trigger("set_revised_salary");
			});
	},

	promotion_details_remove: function (frm) {
		frm.trigger("set_revised_salary");
	},

	employee_property_added: function (frm) {
		// a changed grade, department or designation can change what the formulas pay
		frm.trigger("set_revised_salary");

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
		frm.trigger("set_revised_salary");
		frm.trigger("show_assignment_hint");
	},

	revised_base: function (frm) {
		frm.trigger("set_revised_salary");
		frm.trigger("show_assignment_hint");
	},

	set_revised_salary: function (frm) {
		if (frm.doc.docstatus !== 0) return;

		if (!frm.doc.salary_structure || !frm.doc.revised_base) {
			set_ctc_breakup(frm, []);
			// clear only a calculated CTC; one typed by hand stays
			if (frm.revised_ctc_is_calculated) {
				frm.revised_ctc_is_calculated = false;
				frm.set_value("revised_ctc", null);
			}
			return;
		}

		const sent = revised_salary_inputs(frm);
		frappe
			.call({
				method: "hrms.hr.doctype.employee_promotion.employee_promotion.get_revised_salary_details",
				args: { promotion: frm.doc },
			})
			.then((r) => {
				if (!r.message || revised_salary_inputs(frm) !== sent) return;

				frm.revised_ctc_is_calculated = true;
				frm.set_value("revised_ctc", r.message.ctc || 0).then(() => {
					set_ctc_breakup(frm, r.message.components || []);
					render_promotion_letter_preview(frm);
				});
			});
	},
});

function get_revised_assignment(frm) {
	return frm.doc.__onload?.salary_structure_assignment;
}

// an HTML field, because Frappe's linked-document checks query every Link field, virtual ones included
function render_revised_assignment(frm) {
	const field = frm.get_field("revised_salary_structure_assignment");
	const assignment = get_revised_assignment(frm);
	if (!assignment) {
		field.$wrapper.empty();
		return;
	}

	const [status, color] = assignment.docstatus === 0 ? [__("Draft"), "red"] : [__("Submitted"), "blue"];
	field.$wrapper.html(`
		<div class="form-group">
			<div class="clearfix">
				<label class="control-label">${__("Revised Salary Structure Assignment")}</label>
			</div>
			<div class="control-value like-disabled-input">
				${frappe.utils.get_form_link("Salary Structure Assignment", assignment.name, true)}
				<span class="indicator-pill ${color} ml-2">${status}</span>
			</div>
		</div>
	`);
}

function add_assignment_button(frm) {
	const { docstatus, salary_structure, revised_base } = frm.doc;
	if (
		docstatus !== 1 ||
		!salary_structure ||
		!revised_base ||
		get_revised_assignment(frm) ||
		!frappe.model.can_create("Salary Structure Assignment")
	)
		return;

	frm.add_custom_button(__("Create Salary Structure Assignment"), () => {
		frappe.model.open_mapped_doc({
			method: "hrms.hr.doctype.employee_promotion.employee_promotion.make_salary_structure_assignment",
			frm: frm,
		});
	});
}

function add_email_letter_button(frm) {
	if (frm.doc.docstatus !== 1 || !frm.perm[0]?.email) return;

	frm.add_custom_button(__("Email Promotion Letter"), () => email_promotion_letter(frm));
}

function email_promotion_letter(frm) {
	const designation = get_new_designation(frm.doc);

	hrms.print_utils.email_with_print(frm, {
		subject: designation ? __("Promotion to {0}", [designation]) : __("Promotion Letter"),
		recipients: frm.doc.employee_email || "",
		message: promotion_letter_message(frm.doc, designation),
		print_format: frm.doc.letter_print_format || "Promotion Letter with Salary Break-up",
	});
}

function render_promotion_letter_preview(frm) {
	// rendering runs the print format on the server, so a hidden preview is emptied
	// and the tab change renders it
	const visible = frm.get_field("letter_preview").$wrapper.is(":visible");
	hrms.print_utils.render_print_preview(
		frm,
		"letter_preview",
		visible && frm.doc.docstatus !== 2 ? frm.doc.letter_print_format : null,
	);
}

const render_preview_after_typing = frappe.utils.debounce(render_promotion_letter_preview, 800);

function get_new_designation(doc) {
	return (doc.promotion_details || []).find((row) => row.fieldname === "designation")?.new;
}

function promotion_letter_message(doc, designation) {
	const escape = frappe.utils.escape_html;
	const date = frappe.datetime.global_date_format(doc.promotion_date);

	const lines = [
		__("Dear {0},", [escape(doc.employee_name)]),
		designation
			? __(
					"Congratulations on your promotion to {0}, with effect from {1}. Please find your promotion letter attached.",
					[escape(designation), date],
			  )
			: __(
					"Congratulations on your promotion, with effect from {0}. Please find your promotion letter attached.",
					[date],
			  ),
		__("Regards,"),
	];

	return lines.map((line) => `<p>${line}</p>`).join("");
}

function set_ctc_breakup(frm, rows) {
	if (!rows.length && !(frm.doc.ctc_breakup || []).length) return;

	frm.clear_table("ctc_breakup");
	rows.forEach((row) => frm.add_child("ctc_breakup", row));
	frm.refresh_field("ctc_breakup");
	frm.layout.refresh_dependency();
}

function revised_salary_inputs(frm) {
	const { employee, promotion_date, salary_structure, revised_base } = frm.doc;
	const details = (frm.doc.promotion_details || []).map((row) => [row.fieldname, row.new]);
	return JSON.stringify([employee, promotion_date, salary_structure, revised_base, details]);
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
