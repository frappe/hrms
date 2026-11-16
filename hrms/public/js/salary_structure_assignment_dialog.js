import { RecordTabsDialog, insert_quietly, is_editable } from "./record_tabs_dialog.js";

const FIXED_FIELDS = ["employee", "company"];

export class SalaryStructureAssignmentDialog extends RecordTabsDialog {
	constructor({ assignment, on_saved }) {
		super("Salary Structure Assignment", assignment);
		this.on_saved = on_saved;
	}

	make_tabs() {
		return this.make_field_tabs(
			(df) => is_editable(df) && !FIXED_FIELDS.includes(df.fieldname),
		);
	}

	get_actions() {
		return [
			{ label: __("Save"), onclick: () => this.save() },
			{ label: __("Submit"), variant: "solid", onclick: () => this.save({ submit: true }) },
		];
	}

	get_profile() {
		return { name: this.doc.employee_name, email: this.doc.employee };
	}

	async save({ submit = false } = {}) {
		const values = this.get_doc();
		if (!values) return;
		delete values.name;
		const doc = await insert_quietly({ ...values, docstatus: submit ? 1 : 0 });
		if (!doc) return;
		this.dialog.hide();
		this.on_saved(doc);
	}
}
