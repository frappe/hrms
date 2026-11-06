import { RecordTabsDialog, is_editable, make_panel_body } from "./record_tabs_dialog.js";

const FIXED_FIELDS = ["job_offer", "employee_preboarding", "employee", "company"];

export class AppointmentLetterDialog extends RecordTabsDialog {
	constructor({ letter, on_save, on_sent }) {
		super("Appointment Letter", letter);
		this.template = letter.appointment_letter_template;
		this.shift_type = letter.shift_type;
		this.on_save = on_save;
		this.on_sent = on_sent;
	}

	make_tabs() {
		this.$preview = make_panel_body();
		return [
			...this.make_field_tabs(
				(df) => is_editable(df) && !FIXED_FIELDS.includes(df.fieldname),
			),
			{
				label: __("Preview"),
				content: this.$preview,
				on_activate: () => this.render_preview(),
			},
		];
	}

	prepare_field(df) {
		const source = df.fetch_from?.split(".")[0];
		return source && !df.fetch_if_empty && this.doc[source] ? { ...df, read_only: 1 } : df;
	}

	setup_group(group) {
		this.watch_fields(group, {
			applicant_name: () => this.render_profile(),
			applicant_email: () => this.render_profile(),
			appointment_letter_template: () => this.load_template_body(),
			shift_type: () => this.load_shift_times(),
			start_time: () => this.set_working_hours(),
			end_time: () => this.set_working_hours(),
		});
	}

	get_actions() {
		return [
			{ label: __("Save"), onclick: () => this.save() },
			{ label: __("Send"), variant: "solid", onclick: () => this.send() },
		];
	}

	get_profile() {
		return {
			name: this.get_value("applicant_name"),
			email: this.get_value("applicant_email"),
		};
	}

	async load_template_body() {
		const template = this.get_value("appointment_letter_template");
		if (!template || template === this.template) return;
		this.template = template;
		const { message } = await frappe.db.get_value(
			"Appointment Letter Template",
			template,
			"letter_body",
		);
		this.set_value("letter_body", message.letter_body);
	}

	async load_shift_times() {
		const shift_type = this.get_value("shift_type");
		if (!shift_type || shift_type === this.shift_type) return;
		this.shift_type = shift_type;
		const { message } = await frappe.db.get_value("Shift Type", shift_type, [
			"start_time",
			"end_time",
		]);
		await this.set_value("start_time", message.start_time);
		await this.set_value("end_time", message.end_time);
	}

	set_working_hours() {
		const start = this.get_value("start_time");
		const end = this.get_value("end_time");
		if (!start || !end) return;
		const seconds = (time) => moment.duration(time).asSeconds();
		const day = 24 * 60 * 60;
		const worked = (((seconds(end) - seconds(start)) % day) + day) % day;
		this.set_value("working_hours", flt(worked / 3600, 2));
	}

	render_preview() {
		const doc = this.get_doc({ validate: false });
		hrms.print_utils.render_print_html(
			this.$preview,
			doc,
			doc.appointment_letter_print_format,
		);
	}

	async persist() {
		const doc = this.get_doc();
		if (!doc) return null;
		const method = this.doc.__islocal ? "frappe.client.insert" : "frappe.client.save";
		if (this.doc.__islocal) delete doc.name;
		this.doc = await frappe.xcall(method, { doc });
		return this.doc;
	}

	async save() {
		if (!(await this.persist())) return;
		this.dialog.hide();
		this.on_save();
	}

	async send() {
		const letter = await this.persist();
		if (!letter) return;
		this.dialog.hide();
		this.on_save();
		hrms.appointment_letter.email(make_composer_form(letter, this.on_sent));
	}
}

function make_composer_form(doc, on_sent) {
	return {
		doctype: doc.doctype,
		docname: doc.name,
		doc,
		meta: frappe.get_meta(doc.doctype),
		perm: frappe.perm.get_perm(doc.doctype, doc),
		email_field: "applicant_email",
		events: {},
		wrapper: $(),
		timeline: { get_recipient: () => doc.applicant_email, get_last_email: () => null },
		attachments: { attachment_uploaded() {} },
		get_files: () => [],
		reload_doc: on_sent,
	};
}
