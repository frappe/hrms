import { get_action_handler } from "./onboarding_actions.js";

frappe.provide("hrms.ui");

const ROW_CLICK_KEY = "employee_onboarding_checklist_row_click";

const STATUS = { "In Progress": "in_progress", Stuck: "stuck" };

const ROW_STATUS = { in_progress: "In Progress", stuck: "Stuck" };

hrms.ui.EmployeeOnboardingChecklist = class EmployeeOnboardingChecklist {
	constructor({ frm }) {
		this.frm = frm;
		this.checklist = new frappe.ui.Checklist({
			title: __("Onboarding Checklist"),
			row_click: get_row_click(),
			on_skip: (item) => this.call("skip_activity", { row: item.id }),
			on_unskip: (item) => this.call("unskip_activity", { row: item.id }),
			on_assign: (item, user) => this.call("assign_activity", { row: item.id, user }),
			on_due_date_change: (item, due_date) =>
				this.call("set_activity_due_date", { row: item.id, due_date }),
			on_status_change: (item, status) =>
				this.call("set_activity_progress", {
					row: item.id,
					status: ROW_STATUS[status] || null,
				}),
		});
	}

	render() {
		const $wrapper = this.frm.fields_dict.onboarding_checklist.$wrapper;
		if (!$.contains($wrapper[0], this.checklist.el)) {
			this.$hint = $('<div class="eoc-template-hint"></div>');
			$wrapper.empty().append(this.make_demo_switch(), this.$hint, this.checklist.$el);
		}
		this.render_template_hint();
		this.checklist.set_items((this.frm.doc.activities || []).map((row) => this.get_item(row)));
	}

	// Until the default template gets tasks of the company's own, point first-time users at it.
	render_template_hint() {
		const template = this.frm.doc.__onload?.template_hint;
		this.$hint.empty();
		if (!template) return;

		this.$hint.append(
			frappe.ui.alert({
				title: __("These are the standard onboarding tasks"),
				description: __("Edit the template to add your own tasks, owners and due dates."),
				footer: frappe.ui.button({
					label: __("Edit Template"),
					onclick: () =>
						frappe.set_route("Form", "Employee Onboarding Template", template),
				}),
			}),
		);
	}

	// Demo only: flips the checklist between action buttons and clickable rows.
	make_demo_switch() {
		const tabs = new frappe.ui.TabButtons({
			label: __("Checklist style"),
			options: [
				{ label: __("Buttons"), value: "buttons" },
				{ label: __("Clickable rows"), value: "rows" },
			],
			value: get_row_click() ? "rows" : "buttons",
			on_change: (value) => {
				try {
					localStorage.setItem(ROW_CLICK_KEY, value === "rows" ? "1" : "0");
				} catch (e) {}
				this.checklist.set_row_click(value === "rows");
			},
		});
		return $('<div class="eoc-demo-switch"></div>').append(tabs.$el);
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
			actions: handler.get_actions(this, row, state),
		};
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

function get_row_click() {
	try {
		return localStorage.getItem(ROW_CLICK_KEY) === "1";
	} catch (e) {
		return false;
	}
}
