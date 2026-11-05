// Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Appointment Letter", {
	setup: function (frm) {
		frm.email_field = "applicant_email";
	},

	onload: function (frm) {
		set_default_template(frm);
		frm.set_query("appointment_letter_print_format", function () {
			return { filters: { doc_type: "Appointment Letter", disabled: 0 } };
		});

		frm.set_query("job_offer", function () {
			return { filters: { company: frm.doc.company, docstatus: 1 } };
		});

		frm.set_query("employee", function () {
			return { filters: { company: frm.doc.company } };
		});
	},

	refresh: function (frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Email Appointment Letter"), () =>
				email_appointment_letter(frm),
			);
		}
		render_appointment_letter_preview(frm);
	},

	on_tab_change: function (frm) {
		if (frm.get_active_tab()?.df?.fieldname === "printing_tab") {
			render_appointment_letter_preview(frm);
		}
	},

	appointment_letter_print_format: function (frm) {
		render_appointment_letter_preview(frm);
	},

	letter_head: function (frm) {
		render_appointment_letter_preview(frm);
	},

	signature: function (frm) {
		render_appointment_letter_preview(frm);
	},

	employee: function (frm) {
		if (frm.doc.employee) frm.call("set_shift_from_employee");
	},

	appointment_date: function (frm) {
		if (frm.doc.employee) frm.call("set_shift_from_employee");
	},

	start_time: function (frm) {
		set_working_hours(frm);
	},

	end_time: function (frm) {
		set_working_hours(frm);
	},

	appointment_letter_template: async function (frm) {
		if (!frm.doc.appointment_letter_template) return;
		const { message } = await frappe.db.get_value(
			"Appointment Letter Template",
			frm.doc.appointment_letter_template,
			"letter_body",
		);
		frm.set_value("letter_body", message.letter_body);
	},
});

function set_working_hours(frm) {
	if (!frm.doc.start_time || !frm.doc.end_time) return;
	const seconds = (time) => moment.duration(time).asSeconds();
	const day = 24 * 60 * 60;
	const worked = (((seconds(frm.doc.end_time) - seconds(frm.doc.start_time)) % day) + day) % day;
	frm.set_value("working_hours", flt(worked / 3600, 2));
}

async function set_default_template(frm) {
	if (!frm.is_new() || frm.doc.letter_body || frm.doc.appointment_letter_template) return;
	const { message: template } = await frappe.db.get_value(
		"Appointment Letter Template",
		{ is_default: 1 },
		"name",
	);
	if (template?.name) frm.set_value("appointment_letter_template", template.name);
}

async function email_appointment_letter(frm) {
	const composer = new frappe.views.CommunicationComposer({
		doc: frm.doc,
		frm: frm,
		subject: __("Letter of Appointment - {0}", [frm.doc.applicant_name]),
		recipients: frm.doc.applicant_email,
		attach_document_print: true,
		message: appointment_letter_message(frm.doc),
	});
	composer.dialog.no_focus = true;

	await composer.dialog.set_value(
		"select_print_format",
		frm.doc.appointment_letter_print_format || "Appointment Letter Classic",
	);
	composer.render_print_card_meta();
	composer.sync_print_menu?.();
}

function appointment_letter_message(doc) {
	const escape = frappe.utils.escape_html;
	const blank_line = "<p><br></p>";
	const paragraphs = [
		__("Dear {0},", [escape(doc.applicant_name)]),
		__(
			"Please find attached your letter of appointment with {0}, which sets out the terms and conditions of your employment.",
			[escape(doc.company)],
		),
		__("Please sign and return a copy of the letter as a token of your acceptance."),
	];
	return (
		paragraphs.map((line) => `<p>${line}</p>`).join(blank_line) +
		blank_line.repeat(2) +
		`<p>${__("Regards,")}</p>`
	);
}

let appointment_letter_preview_request = 0;

async function render_appointment_letter_preview(frm) {
	const field = frm.get_field("appointment_letter_preview");
	const $wrapper = field.$wrapper;
	const request = ++appointment_letter_preview_request;
	if (!frm.doc.appointment_letter_print_format) {
		$wrapper.empty();
		return;
	}

	const { message } = await frappe.call({
		method: "frappe.www.printview.get_html_and_style",
		args: {
			doc: frm.doc,
			print_format: frm.doc.appointment_letter_print_format,
			letterhead: frm.doc.letter_head,
			no_letterhead: frm.doc.letter_head ? 0 : 1,
		},
	});
	if (request !== appointment_letter_preview_request || !message) return;

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

	const $head = $(`<div class="text-base-medium mb-3">${__(field.df.label)}</div>`);
	$wrapper.empty().append($head, $iframe);
}
