// Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Appointment Letter", {
	setup: function (frm) {
		frm.email_field = "applicant_email";
	},

	onload: function (frm) {
		set_default_template(frm);
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
				hrms.appointment_letter.email(frm),
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

function render_appointment_letter_preview(frm) {
	hrms.print_utils.render_print_preview(
		frm,
		"appointment_letter_preview",
		frm.doc.appointment_letter_print_format,
	);
}
