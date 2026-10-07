import { get_action_handler } from "./onboarding_actions.js";

frappe.provide("hrms.ui");

const STATUS = { Completed: "done", Skipped: "skipped" };

hrms.ui.EmployeeOnboardingChecklist = class EmployeeOnboardingChecklist {
	constructor({ frm }) {
		this.frm = frm;
		this.checklist = new frappe.ui.Checklist({
			title: __("Onboarding Checklist"),
			on_skip: (item) => this.call("skip_activity", { row: item.id }),
			on_assign: (item, user) => this.call("assign_activity", { row: item.id, user }),
			on_due_date_change: (item, due_date) =>
				this.call("set_activity_due_date", { row: item.id, due_date }),
		});
	}

	render() {
		const $wrapper = this.frm.fields_dict.onboarding_checklist.$wrapper;
		if (!$.contains($wrapper[0], this.checklist.el))
			$wrapper.empty().append(this.checklist.$el);
		this.checklist.set_items((this.frm.doc.activities || []).map((row) => this.get_item(row)));
	}

	get_item(row) {
		const handler = get_action_handler(row.action);
		const status = STATUS[row.status] || "pending";
		const saved = !this.frm.is_new() && !row.__islocal;

		return {
			id: row.name,
			label: __(row.activity_name),
			status,
			description: row.description && frappe.utils.html2text(row.description),
			value: handler.get_value(this, row),
			assignee: row.user,
			due_date: row.due_date,
			locked: this.get_lock_reason(row) || handler.get_lock_reason?.(this, row),
			skippable: saved,
			actions: handler.get_actions(this, row, status),
		};
	}

	get_lock_reason(row) {
		if (!row.depends_on_activity) return null;

		const needed = (this.frm.doc.activities || []).find(
			(other) => other.activity === row.depends_on_activity,
		);
		if (!needed || needed.status === "Completed") return null;
		return __("Needs: {0}", [__(needed.activity_name)]);
	}

	get_offer_default(doctype) {
		return this.frm.doc.__onload?.offer_defaults?.[doctype];
	}

	// Activity methods write their row straight to the database, so the form reloads rather
	// than saves; another user may be working on the same onboarding.
	async call(method, args = {}, freeze_message) {
		await this.save_if_dirty();
		await this.frm.call({ method, doc: this.frm.doc, args, freeze: true, freeze_message });
		await this.frm.reload_doc();
	}

	async save_if_dirty() {
		if (this.frm.is_new() || this.frm.is_dirty()) await this.frm.save();
	}
};
