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
		set_per_cycle_label(frm);

		// Changing the basis triggers the break-up itself, so only recompute when it did not
		// change (the structure was swapped for another while the basis stayed put).
		if (!set_calculation_basis(frm)) {
			update_compensation(frm);
		}
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
		set_per_cycle_label(frm);
		bind_regional_inputs(frm);

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

// Kept on the (ERPNext-era) namespace because it predates this work and a site's Client
// Script may call it. Everything below is new here, so it stays file-scoped.
erpnext.job_offer.make_employee = function (frm) {
	frappe.model.open_mapped_doc({
		method: "hrms.hr.doctype.job_offer.job_offer.make_employee",
		frm: frm,
	});
};

function set_calculation_basis(frm) {
	// Follows the salary structure rather than being a stored default: an offer that carries
	// no structure must not ask for a base at all. Returns whether the value changed, since
	// changing it already triggers a recompute.
	const basis = frm.doc.calculate_component_amount_from;

	if (!frm.doc.salary_structure) {
		if (!basis) return false;
		frm.set_value("calculate_component_amount_from", "");
		return true;
	}

	if (basis) return false;

	frm.set_value("calculate_component_amount_from", "Base and Variable");
	return true;
}

function clear_compensation(frm) {
	if (!(frm.doc.ctc_breakup || []).length && !frm.doc.ctc) return;

	frm.clear_table("ctc_breakup");
	frm.refresh_field("ctc_breakup");
	frm.set_value("ctc", 0);
}

function update_compensation(frm) {
	if (frm.__updating_compensation) return;

	if (!frm.doc.salary_structure) {
		clear_compensation(frm);
		return;
	}

	if (!frm.doc.calculate_component_amount_from) return;

	const driver = frm.doc.calculate_component_amount_from === "CTC" ? frm.doc.ctc : frm.doc.base;
	if (!driver) return;

	const release = () => (frm.__updating_compensation = false);
	frm.__updating_compensation = true;

	frappe.call({
		method: "hrms.hr.doctype.job_offer.job_offer.get_compensation_details",
		args: { offer: frm.doc },
		error: release,
		callback: function (r) {
			if (!r.message) return release();

			const details = r.message;
			frm.set_value({ base: details.base, ctc: details.ctc }).then(() => {
				frm.clear_table("ctc_breakup");
				details.components.forEach((row) => frm.add_child("ctc_breakup", row));
				frm.refresh_field("ctc_breakup");
				release();

				if (details.ctc_adjusted) {
					frappe.show_alert({
						message: __(
							"CTC set to {0}, the closest this salary structure can produce.",
							[format_currency(details.ctc, frm.doc.currency)],
						),
						indicator: "orange",
					});
				}
			});
		},
	});
}

const bound_regional_inputs = new Set();

function bind_regional_inputs(frm) {
	// A regional app adds its own statutory config to the offer (India's EPF Applicable, for
	// one), and the server carries every shared custom field onto the prospective assignment.
	// Those fieldnames are unknown here, so any custom field on the offer re-runs the
	// break-up. Handlers land in a doctype-global registry read at trigger time, hence the
	// module-level guard rather than a per-form one. Layout fields never fire a change, so
	// they need no filtering.
	const handlers = {};

	(frm.meta.fields || []).forEach((df) => {
		if (!df.is_custom_field || bound_regional_inputs.has(df.fieldname)) return;

		bound_regional_inputs.add(df.fieldname);
		handlers[df.fieldname] = (frm) => update_compensation(frm);
	});

	if (Object.keys(handlers).length) frappe.ui.form.on("Job Offer", handlers);
}

function set_per_cycle_label(frm) {
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
}

const COMPENSATION_INPUTS = [
	"calculate_component_amount_from",
	"base",
	"variable",
	"ctc",
	"company",
	"grade",
	"branch",
	"employment_type",
	"department",
	"designation",
	"date_of_joining",
	"offer_date",
];

frappe.ui.form.on(
	"Job Offer",
	Object.fromEntries(
		COMPENSATION_INPUTS.map((fieldname) => [fieldname, (frm) => update_compensation(frm)]),
	),
);
