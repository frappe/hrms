import { AppointmentLetterDialog } from "./appointment_letter_dialog.js";
import { CreateEmployeeDialog } from "./create_employee_dialog.js";

// What each onboarding activity action shows and does. A template row names its action;
// the row's value, lock and buttons come from the handler for that action.

const ACTION_HANDLERS = {
	"Create User": {
		get_value: (list) => list.frm.doc.user,
		get_actions: (list, row, state) =>
			state === "done"
				? [open_action("User", list.frm.doc.user)]
				: [{ label: __("Create"), onclick: () => open_user_dialog(list) }],
	},
	"Appointment Letter": {
		get_value: (list, row) => {
			const sent_on = list.frm.doc.appointment_letter_sent_on;
			if (sent_on)
				return __("Sent on {0}", [frappe.datetime.str_to_user(sent_on, false, true)]);
			return get_letter(list);
		},
		get_actions: (list, row, state) => {
			const letter = get_letter(list);
			if (state === "done") return letter ? [open_action("Appointment Letter", letter)] : [];
			const label = letter ? __("Send") : __("Create");
			return [{ label, onclick: () => open_letter_dialog(list) }];
		},
	},
	"Create Employee": {
		get_value: (list, row) => row.reference_name,
		get_actions: (list, row, state) =>
			state === "done"
				? [open_action("Employee", row.reference_name)]
				: [{ label: __("Create"), onclick: () => create_employee(list) }],
	},
	"Set Roles": {
		get_value: (list) => {
			const set_on = list.frm.doc.roles_set_on;
			return set_on && __("Set on {0}", [frappe.datetime.str_to_user(set_on, false, true)]);
		},
		get_actions: (list, row, state) => {
			if (state === "done") return [open_action("User", list.frm.doc.user)];
			if (!is_open(state)) return [];
			return [{ label: __("Set"), onclick: () => open_roles_dialog(list) }];
		},
	},
	Assign: {
		get_value: (list, row) => {
			if (row.reference_name) return row.reference_name;
			const draft = get_draft(list, row);
			if (draft) return __("Draft {0} to submit", [draft]);
			return list.get_offer_default(row.reference_doctype)?.value;
		},
		get_actions: (list, row, state) => {
			if (row.reference_name)
				return [open_action(row.reference_doctype, row.reference_name)];
			if (!is_open(state)) return [];
			const draft = get_draft(list, row);
			if (draft)
				return [{ ...open_action(row.reference_doctype, draft), label: __("Open Draft") }];
			return [{ label: __("Assign"), onclick: () => assign(list, row) }];
		},
	},
	Manual: {
		get_value: () => null,
		get_actions: (list, row, state) => {
			if (is_open(state))
				return [
					{
						label: __("Mark Done"),
						onclick: () => list.call("complete_activity", { row: row.name }),
					},
				];
			if (state === "done" && list.is_started())
				return [
					{
						label: __("Undo"),
						variant: "subtle",
						onclick: () => list.call("reopen_activity", { row: row.name }),
					},
				];
			return [];
		},
	},
};

function get_letter(list) {
	return list.frm.doc.__onload?.appointment_letter;
}

function get_draft(list, row) {
	return list.frm.doc.__onload?.draft_assignments?.[row.reference_doctype];
}

function is_open(state) {
	return state === "open";
}

export function get_action_handler(action) {
	return ACTION_HANDLERS[action] || ACTION_HANDLERS.Manual;
}

function open_action(doctype, name) {
	return {
		label: __("Open"),
		variant: "subtle",
		onclick: () => frappe.set_route("Form", doctype, name),
	};
}

function open_user_dialog(list) {
	const frm = list.frm;
	const dialog = new frappe.ui.Dialog({
		title: __("Create User Login"),
		fields: [
			{
				fieldname: "personal_email",
				label: __("Personal Email"),
				fieldtype: "Data",
				options: "Email",
				default: frm.doc.personal_email,
				mandatory_depends_on: "eval:doc.create_user_for == 'Personal Email'",
			},
			{
				fieldname: "company_email",
				label: __("Company Email"),
				fieldtype: "Data",
				options: "Email",
				default: frm.doc.company_email,
				mandatory_depends_on: "eval:doc.create_user_for == 'Company Email'",
			},
			{
				fieldname: "create_user_for",
				label: __("Create User For"),
				fieldtype: "Select",
				options: ["Company Email", "Personal Email"],
				default: "Company Email",
			},
		],
		primary_action_label: __("Create User Login"),
		primary_action: async (values) => {
			await list.call("create_user", values, __("Creating the user"));
			dialog.hide();
		},
	});
	dialog.show();
}

async function open_roles_dialog(list) {
	await frappe.model.with_doctype("User Role Profile");
	const dialog = new frappe.ui.Dialog({
		title: __("Set Roles and Permissions"),
		fields: [
			{
				fieldname: "role_profiles",
				label: __("Role Profiles"),
				fieldtype: "Table MultiSelect",
				options: "User Role Profile",
				reqd: 1,
			},
			{
				fieldname: "module_profile",
				label: __("Module Profile"),
				fieldtype: "Link",
				options: "Module Profile",
			},
		],
		primary_action_label: __("Apply to User"),
		primary_action: async ({ role_profiles, module_profile }) => {
			const profiles = role_profiles.map((row) => row.role_profile);
			await list.call(
				"set_user_roles",
				{ role_profiles: profiles, module_profile },
				__("Setting roles"),
			);
			dialog.hide();
		},
	});
	dialog.show();
}

async function open_letter_dialog(list) {
	await list.save_if_dirty();
	const name = get_letter(list);
	const letter = name
		? await frappe.db.get_doc("Appointment Letter", name)
		: await frappe.xcall(
				"hrms.hr.doctype.employee_onboarding.employee_onboarding.make_appointment_letter",
				{ source_name: list.frm.doc.name },
		  );
	new AppointmentLetterDialog({
		letter,
		on_save: () => list.frm.reload_doc(),
		on_sent: () => list.frm.reload_doc(),
	}).show();
}

async function create_employee(list) {
	await list.save_if_dirty();
	const doc = await frappe.xcall(
		"hrms.hr.doctype.employee_onboarding.employee_onboarding.make_employee",
		{ source_name: list.frm.doc.name },
	);
	new CreateEmployeeDialog({
		employee: doc,
		on_created: () => list.frm.reload_doc(),
	}).show();
}

// Reuses the Employee form's assignment engine, so the dialog keeps its Submit step, its
// field hints and its queries. The row is ticked by reconciliation against the real
// assignment document, not by this callback.
function assign(list, row) {
	const doc = list.frm.doc;
	const action = hrms.assignments
		.get_assignment_actions()
		.find((candidate) => candidate.doctype === row.reference_doctype);
	if (!action) {
		frappe.ui.toast({
			message: __("No assignment is available for {0}", [__(row.activity_name)]),
		});
		return;
	}

	const offer_default = list.get_offer_default(row.reference_doctype);
	const defaults = offer_default ? { [offer_default.fieldname]: offer_default.value } : {};
	const ctx = {
		employee: doc.employee,
		employee_name: doc.employee_name,
		company: doc.company,
		date_of_joining: doc.date_of_joining,
	};
	hrms.assignments.open_assignment(ctx, {
		...action,
		prefill: (ctx) => ({ ...action.prefill(ctx), ...defaults }),
		redirect: false,
		on_hide: () => frappe.after_ajax(() => list.call("sync_activities")),
	});
}
