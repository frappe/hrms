import { get_action_handler } from "./preboarding_actions.js";

frappe.provide("hrms.ui");

const STATUS = { "In Progress": "in_progress", Stuck: "stuck" };

const ROW_STATUS = { in_progress: "In Progress", stuck: "Stuck" };

hrms.ui.EmployeePreboardingChecklist = class EmployeePreboardingChecklist {
	constructor({ frm }) {
		this.frm = frm;
		this.checklist = new frappe.ui.Checklist({
			title: __("Preboarding Checklist"),
			add_label: __("Add activity"),
			on_remove: (item) => this.update_row("remove_activity", { row: item.id }),
			on_skip: (item) => this.call("skip_activity", { row: item.id }),
			on_unskip: (item) => this.call("unskip_activity", { row: item.id }),
			on_assign: (item, user) => this.update_row("assign_activity", { row: item.id, user }),
			on_due_date_change: (item, due_date) =>
				this.update_row("set_activity_due_date", { row: item.id, due_date }),
			on_status_change: (item, status) =>
				this.update_row("set_activity_progress", {
					row: item.id,
					status: ROW_STATUS[status] || null,
				}),
		});
	}

	render() {
		const $wrapper = this.frm.fields_dict.preboarding_checklist.$wrapper;
		if (!$.contains($wrapper[0], this.checklist.el)) {
			$wrapper.empty().append(this.checklist.$el);
		}
		const editable = this.can_edit_activities();
		this.checklist.opts.on_add = editable
			? (label) => this.update_row("add_activity", { activity_name: label })
			: null;
		this.checklist.opts.on_reorder = editable
			? (ids) => this.update_row("reorder_activities", { rows: ids })
			: null;
		this.checklist.set_items((this.frm.doc.activities || []).map((row) => this.get_item(row)));
	}

	get_item(row) {
		const handler = get_action_handler(row.action);
		const state = row.completed ? "done" : row.skipped ? "skipped" : "open";
		const saved = !this.frm.is_new() && !row.__islocal;

		return {
			id: row.name,
			label: __(row.activity_name),
			done: Boolean(row.completed),
			skipped: Boolean(row.skipped),
			status: STATUS[row.status],
			description: row.description && frappe.utils.html2text(row.description),
			value: handler.get_value(this, row),
			assignee: row.user,
			due_date: row.due_date,
			locked: this.get_lock_reason(row) || handler.get_lock_reason?.(this, row),
			skippable: saved,
			removable: saved && Boolean(row.added_on_preboarding) && this.can_edit_activities(),
			actions: handler.get_actions(this, row, state),
		};
	}

	can_edit_activities() {
		return this.frm.doc.docstatus === 0 && this.frm.has_perm("write");
	}

	get_lock_reason(row) {
		if (!row.depends_on_action) return null;

		const needed = (this.frm.doc.activities || []).find(
			(other) => other.action === row.depends_on_action,
		);
		if (!needed || needed.completed) return null;
		return __("Needs: {0}", [__(needed.activity_name)]);
	}

	get_offer_default(doctype) {
		return this.frm.doc.__onload?.offer_defaults?.[doctype];
	}

	// Activity methods write their row straight to the database, so the form reloads rather
	// than saves; another user may be working on the same preboarding.
	async call(method, args = {}, freeze_message) {
		await this.save_if_dirty();
		await this.frm.call({ method, doc: this.frm.doc, args, freeze: true, freeze_message });
		await this.frm.reload_doc();
	}

	async update_row(method, args) {
		await this.save_if_dirty();
		await this.frm.call({ method, doc: this.frm.doc, args });
		this.render();
	}

	async save_if_dirty() {
		if (this.frm.is_new() || this.frm.is_dirty()) await this.frm.save();
	}
};
