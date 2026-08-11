// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide("erpnext.job_offer");

frappe.ui.form.on("Job Offer", {
	onload: function (frm) {
		frm.set_query("select_terms", function () {
			return { filters: { hr: 1 } };
		});

		frm.set_query("salary_structure", function () {
			return {
				filters: {
					company: frm.doc.company,
					docstatus: 1,
					is_active: "Yes",
				},
			};
		});

		frm.set_query("department", function () {
			return { filters: { company: frm.doc.company } };
		});

		frm.set_query("reports_to", function () {
			return { filters: { company: frm.doc.company, status: "Active" } };
		});
	},

	setup: function (frm) {
		frm.email_field = "applicant_email";
	},

	salary_structure: function (frm) {
		erpnext.job_offer.set_per_cycle_label(frm);
		erpnext.job_offer.fetch_ctc_breakup(frm);
	},

	base: function (frm) {
		erpnext.job_offer.fetch_ctc_breakup(frm);
	},

	variable: function (frm) {
		erpnext.job_offer.fetch_ctc_breakup(frm);
	},

	ctc_breakup_remove: function (frm) {
		erpnext.job_offer.recalculate_ctc(frm);
	},

	select_terms: function (frm) {
		erpnext.utils.get_terms(frm.doc.select_terms, frm.doc, function (r) {
			if (!r.exc) {
				frm.set_value("terms", r.message);
			}
		});
	},
	job_offer_term_template: function (frm) {
		if (!frm.doc.job_offer_term_template) return;

		frappe.db
			.get_doc("Job Offer Term Template", frm.doc.job_offer_term_template)
			.then((doc) => {
				frm.clear_table("offer_terms");
				doc.offer_terms.forEach((term) => {
					frm.add_child("offer_terms", term);
				});
				refresh_field("offer_terms");
			});
	},

	refresh: function (frm) {
		erpnext.job_offer.set_per_cycle_label(frm);

		if (
			!frm.doc.__islocal &&
			frm.doc.status == "Accepted" &&
			frm.doc.docstatus === 1 &&
			(!frm.doc.__onload || !frm.doc.__onload.employee)
		) {
			frm.add_custom_button(__("Create Employee"), function () {
				erpnext.job_offer.make_employee(frm);
			});
		}

		if (frm.doc.__onload && frm.doc.__onload.employee) {
			frm.add_custom_button(__("Show Employee"), function () {
				frappe.set_route("Form", "Employee", frm.doc.__onload.employee);
			});
		}
	},
});

erpnext.job_offer.make_employee = function (frm) {
	frappe.model.open_mapped_doc({
		method: "hrms.hr.doctype.job_offer.job_offer.make_employee",
		frm: frm,
	});
};

erpnext.job_offer.fetch_ctc_breakup = function (frm) {
	if (!frm.doc.salary_structure || !frm.doc.base) return;

	frappe.call({
		method: "hrms.hr.doctype.job_offer.job_offer.get_ctc_breakup",
		args: {
			salary_structure: frm.doc.salary_structure,
			company: frm.doc.company,
			base: frm.doc.base,
			variable: frm.doc.variable,
			currency: frm.doc.currency,
			from_date: frm.doc.date_of_joining || frm.doc.offer_date,
			department: frm.doc.department,
			designation: frm.doc.designation,
			grade: frm.doc.grade,
			branch: frm.doc.branch,
			employment_type: frm.doc.employment_type,
		},
		callback: function (r) {
			if (!r.message || !r.message.length) return;

			frm.clear_table("ctc_breakup");
			r.message.forEach((row) => frm.add_child("ctc_breakup", row));
			frm.refresh_field("ctc_breakup");
			frm.set_value("ctc", r.message[r.message.length - 1].yearly);
		},
	});
};

erpnext.job_offer.recalculate_ctc = function (frm) {
	const rows = frm.doc.ctc_breakup || [];
	if (rows.length < 2) return;

	const total_row = rows[rows.length - 1];
	let per_cycle = 0;
	let yearly = 0;

	rows.slice(0, -1).forEach((row) => {
		per_cycle += flt(row.per_cycle);
		yearly += flt(row.yearly);
	});

	total_row.per_cycle = per_cycle;
	total_row.yearly = yearly;
	frm.refresh_field("ctc_breakup");
	frm.set_value("ctc", yearly);
};

erpnext.job_offer.set_per_cycle_label = function (frm) {
	if (!frm.doc.salary_structure || !frm.fields_dict.ctc_breakup) return;

	frappe.db
		.get_value("Salary Structure", frm.doc.salary_structure, "payroll_frequency")
		.then((r) => {
			const frequency = r.message && r.message.payroll_frequency;
			if (!frequency) return;

			frm.fields_dict.ctc_breakup.grid.update_docfield_property(
				"per_cycle",
				"label",
				__(frequency),
			);
		});
};

frappe.ui.form.on("Job Offer Component", {
	per_cycle: function (frm) {
		erpnext.job_offer.recalculate_ctc(frm);
	},

	yearly: function (frm) {
		erpnext.job_offer.recalculate_ctc(frm);
	},
});
