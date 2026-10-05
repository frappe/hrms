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

		frm.set_query("offer_letter_print_format", function () {
			return { filters: { doc_type: "Job Offer", disabled: 0 } };
		});

		set_default_leave_and_holidays(frm);
	},

	setup: function (frm) {
		frm.email_field = "applicant_email";
	},

	salary_structure: function (frm) {
		set_per_cycle_label(frm);

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

	leave_policy: function (frm) {
		set_leave_allocations(frm);
	},

	holiday_list: function (frm) {
		set_holiday_summary(frm);
	},

	offer_letter_print_format: function (frm) {
		render_offer_letter_preview(frm);
	},

	signature: function (frm) {
		render_offer_letter_preview(frm);
	},

	letter_head: function (frm) {
		render_offer_letter_preview(frm);
	},

	refresh: function (frm) {
		set_per_cycle_label(frm);
		bind_regional_inputs(frm);
		bind_grade_reselect(frm);
		render_offer_letter_preview(frm);

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

	email_offer_letter: function (frm) {
		email_offer_letter(frm);
	},
});

async function email_offer_letter(frm) {
	const composer = new frappe.views.CommunicationComposer({
		doc: frm.doc,
		frm: frm,
		subject: __("Offer of Employment - {0}", [frm.doc.designation]),
		recipients: frm.doc.applicant_email,
		attach_document_print: true,
		message: offer_letter_message(frm.doc),
	});

	await composer.dialog.set_value(
		"select_print_format",
		frm.doc.offer_letter_print_format || "Job Offer Classic",
	);
	composer.render_print_card_meta();
	composer.sync_print_menu?.();
}

let offer_letter_preview_request = 0;

async function render_offer_letter_preview(frm) {
	const field = frm.get_field("offer_letter_preview");
	const $wrapper = field.$wrapper;
	const $button = frm.get_field("email_offer_letter").$wrapper;
	if (!frm.doc.offer_letter_print_format || frm.doc.docstatus === 2) {
		$button.detach();
		$wrapper.empty();
		return;
	}

	const request = ++offer_letter_preview_request;
	const { message } = await frappe.call({
		method: "frappe.www.printview.get_html_and_style",
		args: {
			doc: frm.doc,
			print_format: frm.doc.offer_letter_print_format,
			letterhead: frm.doc.letter_head,
			no_letterhead: frm.doc.letter_head ? 0 : 1,
		},
	});
	if (request !== offer_letter_preview_request || !message) return;

	const $iframe = $(
		`<iframe sandbox="allow-same-origin" frameborder="0" style="width: 100%; height: 900px; border: 1px solid var(--border-color); border-radius: var(--border-radius-md);"></iframe>`,
	);
	$iframe[0].srcdoc = /^\s*<(!doctype|html)\b/i.test(message.html || "")
		? message.html
		: `<!DOCTYPE html><html><head>
			<link href="${frappe.urllib.get_base_url()}${frappe.assets.bundled_asset(
				"print.bundle.css",
			)}" rel="stylesheet">
			<style>${(message.style || "").replace(/<\//g, "<\\/")}</style>
		</head><body><div class="print-format">${message.html || ""}</div></body></html>`;

	const $head = $(`<div class="flex justify-between align-items-start">
		<div class="text-base-medium mb-3">${__(field.df.label)}</div>
	</div>`).append($button.detach());
	$wrapper.empty().append($head, $iframe);
}

function offer_letter_message(doc) {
	const escape = frappe.utils.escape_html;
	const format_date = (date) => frappe.datetime.global_date_format(date);

	const lines = [
		__("Dear {0},", [escape(doc.applicant_name)]),
		__(
			"We are delighted to offer you the position of {0} at {1}. Please find attached your offer letter, which sets out the details of your role and compensation.",
			[escape(doc.designation), escape(doc.company)],
		),
		doc.offer_valid_till
			? __(
					"This offer is valid until {0}. Please review the letter and confirm your acceptance by then.",
					[format_date(doc.offer_valid_till)],
			  )
			: __("Please review the letter and confirm your acceptance at the earliest."),
		doc.date_of_joining
			? __("We look forward to welcoming you on {0}.", [format_date(doc.date_of_joining)])
			: __("We look forward to welcoming you to the team."),
		__("Regards,"),
	];

	return lines.map((line) => `<p>${line}</p>`).join("");
}

erpnext.job_offer.make_employee = function (frm) {
	frappe.model.open_mapped_doc({
		method: "hrms.hr.doctype.job_offer.job_offer.make_employee",
		frm: frm,
	});
};

function set_calculation_basis(frm) {
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

function bind_grade_reselect(frm) {
	const $input = frm.get_field("grade").$input;
	if (!$input) return;

	$input.off("awesomplete-selectcomplete.base").on("awesomplete-selectcomplete.base", (e) => {
		const grade = e.originalEvent.text.value;
		if (grade === frm.doc.grade) set_base_from_grade(frm, grade);
	});
}

function set_base_from_grade(frm, grade) {
	if (frm.doc.calculate_component_amount_from === "CTC") return;

	frappe.db.get_value("Employee Grade", grade, "default_base_pay").then((r) => {
		const base = r.message && r.message.default_base_pay;
		if (base && base !== frm.doc.base) frm.set_value("base", base);
	});
}

function clear_compensation(frm) {
	if (!(frm.doc.ctc_breakup || []).length && !frm.doc.ctc && !frm.doc.gross) return;

	frm.clear_table("ctc_breakup");
	frm.refresh_field("ctc_breakup");
	frm.set_value({ ctc: 0, gross: 0 });
}

function update_compensation(frm) {
	if (frm.__updating_compensation) {
		frm.__compensation_pending = true;
		return;
	}

	if (!frm.doc.salary_structure) {
		clear_compensation(frm);
		return;
	}

	if (!compensation_driver(frm)) return;

	const was_empty = !(frm.doc.ctc_breakup || []).length;
	const release = hold_compensation(frm);

	frappe.call({
		method: "hrms.hr.doctype.job_offer.job_offer.get_compensation_details",
		args: { offer: frm.doc },
		error: release,
		callback: function (r) {
			if (!r.message) return release();

			apply_compensation(frm, r.message, was_empty).then(release);
		},
	});
}

function compensation_driver(frm) {
	if (!frm.doc.calculate_component_amount_from) return 0;

	return frm.doc.calculate_component_amount_from === "CTC" ? frm.doc.ctc : frm.doc.base;
}

function hold_compensation(frm) {
	const sent = compensation_signature(frm);

	frm.__updating_compensation = true;
	frm.__compensation_pending = false;

	return () => {
		frm.__updating_compensation = false;
		if (!frm.__compensation_pending) return;

		frm.__compensation_pending = false;
		if (compensation_signature(frm) !== sent) update_compensation(frm);
	};
}

function apply_compensation(frm, details, was_empty) {
	return frm
		.set_value({ base: details.base, ctc: details.ctc, gross: details.gross })
		.then(() => {
			frm.clear_table("ctc_breakup");
			details.components.forEach((row) => frm.add_child("ctc_breakup", row));
			frm.refresh_field("ctc_breakup");

			if (was_empty && details.components.length) {
				frm.scroll_to_field("ctc_breakup", false);
			}

			if (details.ctc_adjusted) announce_ctc_adjustment(frm, details.ctc);
		});
}

function announce_ctc_adjustment(frm, ctc) {
	frappe.show_alert({
		message: __("CTC set to {0}, the closest this salary structure can produce.", [
			format_currency(ctc, frm.doc.currency),
		]),
		indicator: "orange",
	});
}

const bound_regional_inputs = new Set();

function bind_regional_inputs(frm) {
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

function compensation_signature(frm) {
	const solved = frm.doc.calculate_component_amount_from === "CTC" ? "base" : "ctc";
	const fields = COMPENSATION_INPUTS.concat(Array.from(bound_regional_inputs)).filter(
		(fieldname) => fieldname !== solved,
	);

	return JSON.stringify(fields.map((fieldname) => frm.doc[fieldname] ?? null));
}

frappe.ui.form.on(
	"Job Offer",
	Object.fromEntries(
		COMPENSATION_INPUTS.map((fieldname) => [fieldname, (frm) => update_compensation(frm)]),
	),
);

function set_leave_allocations(frm) {
	if (!frm.doc.leave_policy) {
		frm.clear_table("leave_allocations");
		frm.refresh_field("leave_allocations");
		return;
	}

	frappe.call({
		method: "hrms.hr.doctype.job_offer.job_offer.get_leave_allocations",
		args: { leave_policy: frm.doc.leave_policy },
		callback: function (r) {
			frm.clear_table("leave_allocations");
			(r.message || []).forEach((row) => frm.add_child("leave_allocations", row));
			frm.refresh_field("leave_allocations");
		},
	});
}

function set_holiday_summary(frm) {
	if (!frm.doc.holiday_list) {
		frm.set_value({ weekly_off_days: "", total_public_holidays: 0 });
		return;
	}

	frappe.call({
		method: "hrms.hr.doctype.job_offer.job_offer.get_holiday_summary",
		args: { holiday_list: frm.doc.holiday_list },
		callback: function (r) {
			if (r.message) frm.set_value(r.message);
		},
	});
}

function set_default_leave_and_holidays(frm) {
	if (!frm.is_new()) return;

	set_latest(frm, "holiday_list", "Holiday List");
	set_latest(frm, "leave_policy", "Leave Policy");
}

function set_latest(frm, fieldname, doctype) {
	if (frm.doc[fieldname]) return;

	frappe.db
		.get_list(doctype, { order_by: "creation desc", limit: 1, pluck: "name" })
		.then((names) => {
			if (names.length && !frm.doc[fieldname]) frm.set_value(fieldname, names[0]);
		});
}
