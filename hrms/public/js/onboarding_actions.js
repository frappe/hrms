import { AppointmentLetterDialog } from "./appointment_letter_dialog.js";
import { CreateEmployeeDialog } from "./create_employee_dialog.js";
import { SalaryStructureAssignmentDialog } from "./salary_structure_assignment_dialog.js";

const PREBOARDING_BADGES = {
	"Awaiting Employee Details": () => ({ label: __("Awaiting employee details"), theme: "blue" }),
	"Details Submitted": () => ({ label: __("Details submitted"), theme: "amber" }),
};

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
		get_badge: (list, row, state) => {
			if (state === "done") return null;
			return PREBOARDING_BADGES[list.frm.doc.boarding_status]?.() || null;
		},
		get_actions: (list, row, state) =>
			state === "done"
				? [open_action("Employee", row.reference_name)]
				: [{ label: __("Create"), onclick: () => create_employee(list) }],
	},
	"Set Roles": {
		get_value: (list) => {
			const access = get_user_access(list);
			const assigned = [...(access.role_profiles || []), ...(access.extra_roles || [])];
			if (assigned.length) return assigned.join(", ");
			return list.frm.doc.roles_set_on ? __("Default roles") : null;
		},
		get_actions: (list, row, state) => {
			if (state === "done")
				return [open_action("User", list.frm.doc.user, "roles_permissions_tab")];
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

function open_action(doctype, name, tab) {
	return {
		label: __("Open"),
		variant: "subtle",
		onclick: () => {
			if (tab) frappe.route_hooks.after_load = (frm) => frm.layout.select_tab(tab);
			frappe.set_route("Form", doctype, name);
		},
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
			show_invite_sent(
				values.create_user_for === "Personal Email"
					? values.personal_email
					: values.company_email,
			);
		},
	});
	dialog.show();
}

function show_invite_sent(email) {
	frappe.msgprint({
		title: __("Welcome email sent"),
		indicator: "green",
		message: __(
			"We sent a welcome email to {0} with a link to the preboarding page where they submit their details and upload required documents.",
			[`<b>${frappe.utils.escape_html(email)}</b>`],
		),
	});
}

async function open_roles_dialog(list) {
	await frappe.model.with_doctype("User Role Profile");
	const access = get_user_access(list);
	const roles = await get_assignable_roles();
	const get_dialog = () => dialog;
	const dialog = new frappe.ui.Dialog({
		title: __("Set Roles and Permissions"),
		size: "large",
		fields: [
			{
				fieldname: "profile_warning",
				fieldtype: "HTML",
				depends_on: "eval:doc.assign_by == 'Role Profiles'",
				options: `<div class="form-group" style="margin-top: -12px">${frappe.ui.alert.html(
					{
						title: __("Role profiles replace all of the user's roles"),
						theme: "yellow",
					},
				)}</div>`,
			},
			{
				fieldname: "assign_by",
				label: __("Assign By"),
				fieldtype: "Select",
				options: [
					{ label: __("Roles"), value: "Roles" },
					{ label: __("Role Profiles"), value: "Role Profiles" },
				],
				default: "Roles",
			},
			roles
				? make_checklist("roles", get_dialog, {
						depends_on: "eval:doc.assign_by == 'Roles'",
						values: roles,
						checked: (role) => (access.roles || []).includes(role),
				  })
				: {
						fieldname: "roles_note",
						fieldtype: "HTML",
						depends_on: "eval:doc.assign_by == 'Roles'",
						options: `<div class="form-group">${frappe.ui.alert.html({
							title: __("Only users who can edit users can change roles"),
							theme: "yellow",
						})}</div>`,
				  },
			{
				fieldname: "role_profiles",
				label: __("Role Profiles"),
				fieldtype: "Table MultiSelect",
				options: "User Role Profile",
				depends_on: "eval:doc.assign_by == 'Role Profiles'",
			},
			{
				fieldname: "module_profile",
				label: __("Module Profile"),
				fieldtype: "Link",
				options: "Module Profile",
				default: access.module_profile,
			},
			...(access.modules
				? [
						make_checklist("modules", get_dialog, {
							label: __("Allow Modules"),
							depends_on: "eval:!doc.module_profile",
							values: access.modules,
							checked: (module) => !(access.blocked_modules || []).includes(module),
						}),
				  ]
				: []),
		],
		primary_action_label: __("Apply"),
		primary_action: async (values) => {
			const args = get_access_args(values, {
				roles: Boolean(roles),
				modules: Boolean(access.modules),
			});
			if (!args) return;
			await list.call("set_user_roles", args, __("Setting roles"));
			dialog.hide();
		},
		secondary_action_label: __("Keep Current Roles"),
		secondary_action: async () => {
			await list.call("set_user_roles", {}, __("Setting roles"));
			dialog.hide();
		},
	});
	dialog.$wrapper.addClass("eo-roles-dialog");
	dialog.show();
}

function make_checklist(fieldname, get_dialog, { label, depends_on, values, checked }) {
	const options = values.map((value) => ({ label: __(value), value, checked: checked(value) }));
	return {
		fieldname,
		label,
		fieldtype: "MultiCheck",
		columns: "12rem 3",
		select_all: true,
		depends_on,
		options,
		on_change: () => {
			const selected = get_dialog().fields_dict[fieldname].selected_options;
			for (const option of options) option.checked = selected.includes(option.value);
		},
	};
}

function get_assignable_roles() {
	if (!frappe.model.can_read("Role")) return null;
	return frappe.xcall("frappe.core.doctype.user.user.get_all_roles");
}

function get_access_args(values, can_edit) {
	const { assign_by, roles, role_profiles, module_profile, modules } = values;
	const args = { module_profile };
	if (can_edit.modules && !module_profile) args.modules = modules || [];
	if (assign_by === "Role Profiles") {
		args.role_profiles = (role_profiles || []).map((row) => row.role_profile);
		if (!args.role_profiles.length) {
			frappe.ui.toast({
				type: "error",
				message: __("Pick a role profile, or keep the current roles"),
			});
			return null;
		}
		args.assign_by = assign_by;
	} else if (can_edit.roles) {
		args.assign_by = assign_by;
		args.roles = roles || [];
	}
	return args;
}

function get_user_access(list) {
	return list.frm.doc.__onload?.user_access || {};
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

function assign(list, row) {
	if (row.reference_doctype === "Salary Structure Assignment")
		return assign_salary_structure(list);
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

async function assign_salary_structure(list) {
	await list.save_if_dirty();
	await frappe.model.with_doctype("Salary Structure Assignment");
	const doc = list.frm.doc;
	const offer_default = list.get_offer_default("Salary Structure Assignment");
	const assignment = Object.assign(
		frappe.model.get_new_doc("Salary Structure Assignment", null, null, true),
		{
			employee: doc.employee,
			employee_name: doc.employee_name,
			company: doc.company,
			from_date: doc.date_of_joining,
		},
		offer_default ? { [offer_default.fieldname]: offer_default.value } : {},
	);
	new SalaryStructureAssignmentDialog({
		assignment,
		on_saved: () => list.call("sync_activities"),
	}).show();
}
