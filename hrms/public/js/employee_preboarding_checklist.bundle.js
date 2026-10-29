import { get_action_handler } from "./preboarding_actions.js";

frappe.provide("hrms.ui");

const STATUS = { "In Progress": "in_progress", Stuck: "stuck" };

const ROW_STATUS = { in_progress: "In Progress", stuck: "Stuck" };

hrms.ui.EmployeePreboardingChecklist = class EmployeePreboardingChecklist {
	constructor({ frm }) {
		this.frm = frm;
	}

	render() {
		const wrapper = this.frm.fields_dict.preboarding_checklist.wrapper;
		const props = this.get_props();
		if (this.island && this.wrapper === wrapper) {
			this.island.update(props);
			return;
		}
		this.island?.unmount();
		this.wrapper = wrapper;
		$(wrapper).empty();
		this.island = frappe.ui.mount_island("hrms.checklist", wrapper, props);
	}

	get_props() {
		const planning = this.is_planning();
		const started = this.is_started();
		return {
			title: __("Preboarding Checklist"),
			addLabel: __("Add activity"),
			items: (this.frm.doc.activities || []).map((row) => this.get_item(row)),
			searchUsers: (txt) => this.search_users(txt),
			onRemove: (row) => this.update_row("remove_activity", { row }),
			onSkip: (row) => this.call("skip_activity", { row }),
			onUnskip: (row) => this.call("unskip_activity", { row }),
			onAdd: planning
				? (label) => this.update_row("add_activity", { activity_name: label })
				: null,
			onReorder: planning ? (rows) => this.update_row("reorder_activities", { rows }) : null,
			onAssign: planning
				? (row, user) => this.update_row("assign_activity", { row, user })
				: null,
			onDueDateChange: planning
				? (row, due_date) => this.update_row("set_activity_due_date", { row, due_date })
				: null,
			onStatusChange: started
				? (row, status) =>
						this.update_row("set_activity_progress", {
							row,
							status: ROW_STATUS[status] || null,
						})
				: null,
		};
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
			assignee: row.user ? this.get_user_option(row.user) : null,
			due_date: row.due_date,
			due_date_label: row.due_date ? frappe.datetime.str_to_user(row.due_date) : "",
			overdue: Boolean(
				row.due_date &&
					frappe.datetime.get_diff(row.due_date, frappe.datetime.get_today()) < 0,
			),
			locked: this.get_lock_reason(row) || handler.get_lock_reason?.(this, row),
			skippable: saved && this.frm.doc.docstatus < 2,
			removable: saved && Boolean(row.added_on_preboarding) && this.is_planning(),
			actions: this.get_actions(handler, row, state).map(({ onclick, ...action }) => ({
				...action,
				onClick: onclick,
			})),
		};
	}

	get_user_option(user, description) {
		const info = frappe.user_info(user);
		return {
			value: user,
			label: description || info.fullname || user,
			description: description ? user : "",
			image: info.image,
		};
	}

	async search_users(txt) {
		const users = await frappe.db.get_link_options(
			"User",
			txt,
			{ user_type: "System User", enabled: 1 },
			20,
		);
		return users.map(({ value, description }) => this.get_user_option(value, description));
	}

	is_planning() {
		return this.frm.doc.docstatus === 0 && this.frm.has_perm("write");
	}

	is_started() {
		return this.frm.doc.docstatus === 1 && this.frm.has_perm("write");
	}

	get_actions(handler, row, state) {
		const actions = handler.get_actions(this, row, state);
		if (this.is_started()) return actions.map((action) => ({ ...action, variant: "solid" }));
		if (state === "done" || row.reference_name) return actions;
		if (!this.is_planning()) return [];
		return actions.map((action) => ({
			...action,
			variant: "subtle",
			onclick: () =>
				frappe.throw({
					title: __("Document submission required"),
					message: __("Submit the preboarding to start its activities"),
				}),
		}));
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
