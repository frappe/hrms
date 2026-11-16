import { RecordTabsDialog, call_quietly, is_editable } from "./record_tabs_dialog.js";

const FIXED_FIELDS = ["employee", "company"];

export class SalaryStructureAssignmentDialog extends RecordTabsDialog {
	constructor({ assignment, on_saved }) {
		super("Salary Structure Assignment", assignment);
		this.on_saved = on_saved;
		this.dirty = true;
	}

	make_tabs() {
		return this.make_field_tabs(
			(df) => is_editable(df) && !FIXED_FIELDS.includes(df.fieldname),
			{ lead: ["salary_structure", "from_date"] },
		);
	}

	prepare_field(df) {
		return { ...df, onchange: () => this.mark_dirty() };
	}

	get_actions() {
		return this.dirty
			? [{ label: __("Save"), variant: "solid", onclick: () => this.save() }]
			: [{ label: __("Submit"), variant: "solid", onclick: () => this.submit() }];
	}

	get_profile() {
		return { name: this.doc.employee_name, email: this.doc.employee };
	}

	async show() {
		await super.show();
		this.ready = true;
	}

	mark_dirty() {
		if (!this.ready || this.dirty) return;
		this.dirty = true;
		this.render_actions();
	}

	async save() {
		const values = this.get_doc();
		if (!values) return;
		const is_new = !!this.doc.__islocal;
		if (is_new) delete values.name;
		const doc = await call_quietly(is_new ? "frappe.client.insert" : "frappe.client.save", {
			doc: values,
		});
		if (!doc) return;
		this.doc = doc;
		this.dirty = false;
		this.render_actions();
		this.on_saved(doc);
	}

	async submit() {
		const doc = await call_quietly("frappe.client.submit", { doc: this.doc });
		if (!doc) return;
		this.dialog.hide();
		this.on_saved(doc);
	}
}
