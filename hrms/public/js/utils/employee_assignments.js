// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

// The assignment engine shared by the Employee form and the Employee Onboarding
// wizard. Callers pass a context of { employee, employee_name, company,
// date_of_joining } rather than a form, so any surface can drive it.

frappe.provide("hrms.assignments");

const assignable_masters = {};

function get_assignment_actions() {
	return [
		{
			label: __("Holiday List"),
			doctype: "Holiday List Assignment",
			master_field: "holiday_list",
			prefill: (ctx) => ({
				applicable_for: "Employee",
				assigned_to: ctx.employee,
				employee_name: ctx.employee_name,
				employee_company: ctx.company,
			}),
			hide: ["naming_series"],
			on_change: {
				holiday_list: sync_holiday_list_range,
				from_date: flag_start_date_outside_range,
			},
		},
		{
			label: __("Leave Policy"),
			doctype: "Leave Policy Assignment",
			master: "Leave Policy",
			master_field: "leave_policy",
			prefill: (ctx) => ({ employee: ctx.employee, assignment_based_on: "Leave Period" }),
			queries: (ctx) => ({
				leave_policy: { docstatus: 1 },
				leave_period: { is_active: 1, company: ctx.company },
			}),
			on_change: {
				assignment_based_on: set_leave_effective_dates,
				leave_period: set_leave_effective_dates,
			},
		},
		{
			label: __("Salary Structure"),
			doctype: "Salary Structure Assignment",
			master: "Salary Structure",
			prefill: (ctx) => ({ employee: ctx.employee, company: ctx.company }),
			redirect: true,
		},
		{
			label: __("Shift"),
			doctype: "Shift Assignment",
			prefill: (ctx) => ({ employee: ctx.employee, company: ctx.company }),
			redirect: true,
		},
		{
			label: __("Shift Schedule"),
			doctype: "Shift Schedule Assignment",
			master: "Shift Schedule",
			prefill: (ctx) => ({ employee: ctx.employee, company: ctx.company }),
			redirect: true,
		},
	];
}

function get_assignable_masters(company) {
	if (!assignable_masters[company]) {
		assignable_masters[company] = frappe
			.xcall("hrms.overrides.employee_master.get_assignable_masters", { company })
			.catch(() => {
				delete assignable_masters[company];
				return {};
			});
	}

	return assignable_masters[company];
}

function open_assignment(ctx, action) {
	if (action.redirect) return frappe.new_doc(action.doctype, action.prefill(ctx));

	frappe.model.with_doctype(action.doctype, () => {
		const doc = Object.assign(
			frappe.model.get_new_doc(action.doctype, null, null, true),
			action.prefill(ctx),
		);

		frappe.ui.form.make_quick_entry(
			action.doctype,
			(created_doc) => {
				notify_assignment_created(action, created_doc);
				action.on_created?.(created_doc);
			},
			(dialog) => setup_dialog(dialog, action, ctx),
			doc,
			true,
		);
	});
}

function setup_dialog(dialog, action, ctx) {
	for (const [fieldname, filters] of Object.entries(action.queries?.(ctx) || {}))
		dialog.set_query(fieldname, () => ({ filters }));

	for (const fieldname of action.hide || []) {
		const control = dialog.fields_dict[fieldname];
		if (!control) continue;

		control.df = { ...control.df, hidden: 1 };
		control.refresh();
	}

	for (const [fieldname, handler] of Object.entries(action.on_change || {})) {
		const control = dialog.fields_dict[fieldname];
		if (!control) continue;

		control.df = { ...control.df, onchange: () => handler(dialog, ctx) };
		if (dialog.get_value(fieldname)) handler(dialog, ctx);
	}

	dialog.add_custom_action(__("Edit Full Form"), () => dialog.open_doc(false));
	keep_dialog_open_for_submit(dialog);
}

function keep_dialog_open_for_submit(dialog) {
	dialog.set_primary_action(__("Save"), () => {
		if (dialog.working || !dialog.get_values()) return;

		dialog.working = true;
		dialog.insert().finally(() => (dialog.working = false));
	});
}

function set_field_hint(dialog, fieldname, title) {
	dialog.modal_body.find(".assignment-hint").remove();
	if (!title) return;

	frappe.ui
		.alert({ title, theme: "blue", css_class: "assignment-hint" })
		.insertAfter(dialog.fields_dict[fieldname].$wrapper);
}

async function sync_holiday_list_range(dialog) {
	const holiday_list = dialog.get_value("holiday_list");
	dialog.holiday_list_range = null;

	if (holiday_list) {
		const response = await frappe.db.get_value("Holiday List", holiday_list, [
			"from_date",
			"to_date",
		]);
		dialog.holiday_list_range = response.message?.from_date ? response.message : null;
	}

	const range_start = dialog.holiday_list_range?.from_date;
	if (range_start && !dialog.get_value("from_date"))
		await dialog.set_value("from_date", range_start);

	flag_start_date_outside_range(dialog);
}

async function set_leave_effective_dates(dialog, ctx) {
	const assignment_based_on = dialog.get_value("assignment_based_on");

	if (!assignment_based_on) {
		await dialog.set_value("effective_from", "");
		await dialog.set_value("effective_to", "");
		return;
	}

	if (assignment_based_on === "Joining Date") {
		await dialog.set_value("effective_from", ctx.date_of_joining);
		await dialog.set_value(
			"effective_to",
			frappe.datetime.add_months(ctx.date_of_joining, 12),
		);
		return;
	}

	const leave_period = dialog.get_value("leave_period");
	if (!leave_period) return;

	const response = await frappe.db.get_value("Leave Period", leave_period, [
		"from_date",
		"to_date",
	]);
	if (!response.message) return;

	await dialog.set_value("effective_from", response.message.from_date);
	await dialog.set_value("effective_to", response.message.to_date);
}

function flag_start_date_outside_range(dialog) {
	const range = dialog.holiday_list_range;
	const from_date = dialog.get_value("from_date");
	if (!range || !from_date) return set_field_hint(dialog, "from_date", null);

	const outside =
		frappe.datetime.get_diff(from_date, range.from_date) < 0 ||
		frappe.datetime.get_diff(from_date, range.to_date) > 0;

	set_field_hint(
		dialog,
		"from_date",
		outside &&
			__("Assignment must start between {0} and {1}", [
				frappe.datetime.str_to_user(range.from_date),
				frappe.datetime.str_to_user(range.to_date),
			]),
	);
}

function notify_assignment_created(action, doc) {
	frappe.quick_entry?.hide();

	const master_doctype = frappe.meta.get_docfield(action.doctype, action.master_field).options;

	frappe.show_alert({
		message: __("{0} was assigned {1}", [
			__(master_doctype),
			frappe.utils.get_form_link(action.doctype, doc.name, true),
		]),
		indicator: "green",
	});
}

Object.assign(hrms.assignments, {
	get_assignment_actions,
	get_assignable_masters,
	open_assignment,
});
