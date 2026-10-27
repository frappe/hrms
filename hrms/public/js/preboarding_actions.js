// What each preboarding activity action shows and does. A template row names its action;
// the row's value, lock and buttons come from the handler for that action.

const USER_FIELDS = ["personal_email", "company_email", "create_user_for"];

const ACTION_HANDLERS = {
	"Create User": {
		get_value: (list) => list.frm.doc.user,
		get_actions: (list, row, state) =>
			state === "done"
				? [open_action("User", list.frm.doc.user)]
				: [{ label: __("Create"), onclick: () => open_fields_dialog(list, user_dialog) }],
	},
	"Appointment Letter": {
		get_value: (list, row) => {
			const sent_on = list.frm.doc.appointment_letter_sent_on;
			if (sent_on)
				return __("Sent on {0}", [frappe.datetime.str_to_user(sent_on, false, true)]);
			return get_letter(list);
		},
		// Appointment Letter still requires a Job Applicant, so an offer without one can't have a letter.
		get_lock_reason: (list) =>
			list.frm.doc.job_applicant ? null : __("Needs a Job Applicant on the Job Offer"),
		get_actions: (list, row, state) => {
			const letter = get_letter(list);
			if (state === "done") return letter ? [open_action("Appointment Letter", letter)] : [];
			if (!letter)
				return [{ label: __("Create"), onclick: () => create_appointment_letter(list) }];
			return [{ label: __("Send"), onclick: () => open_letter_dialog(list) }];
		},
	},
	"Create Employee": {
		get_value: (list, row) => row.reference_name,
		get_actions: (list, row, state) =>
			state === "done"
				? [open_action("Employee", row.reference_name)]
				: [{ label: __("Create"), onclick: () => create_employee(list) }],
	},
	Assign: {
		get_value: (list, row) =>
			row.reference_name || list.get_offer_default(row.reference_doctype)?.value,
		get_actions: (list, row, state) => {
			if (row.reference_name)
				return [open_action(row.reference_doctype, row.reference_name)];
			if (!is_open(state)) return [];
			return [{ label: __("Assign"), onclick: () => assign(list, row) }];
		},
	},
	Manual: {
		get_value: () => null,
		get_actions: (list, row, state) =>
			is_open(state)
				? [
						{
							label: __("Mark Done"),
							onclick: () => list.call("complete_activity", { row: row.name }),
						},
				  ]
				: [],
	},
};

const user_dialog = {
	title: __("Create User Login"),
	fieldnames: USER_FIELDS,
	primary_label: __("Create User Login"),
	method: "create_user",
	freeze_message: __("Creating the user"),
};

function get_letter(list) {
	return list.frm.doc.__onload?.appointment_letter;
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

// The preboarding's own fields, edited in a dialog and saved before the action runs.
function open_fields_dialog(list, { title, fieldnames, primary_label, method, freeze_message }) {
	const frm = list.frm;
	const fields = fieldnames
		.map((fieldname) => frappe.meta.get_docfield(frm.doctype, fieldname, frm.doc.name))
		.filter(Boolean)
		.map((df) => ({
			fieldname: df.fieldname,
			label: df.label,
			fieldtype: df.fieldtype,
			options: df.options,
			reqd: df.reqd,
			mandatory_depends_on: df.mandatory_depends_on,
			default: frm.doc[df.fieldname],
		}));
	if (fields.length > 5)
		fields.splice(Math.ceil(fields.length / 2), 0, { fieldtype: "Column Break" });

	const dialog = new frappe.ui.Dialog({
		title,
		fields,
		size: fields.length > 5 ? "large" : "small",
		primary_action_label: primary_label,
		primary_action: async (values) => {
			await frm.set_value(values);
			await list.call(method, {}, freeze_message);
			dialog.hide();
		},
	});
	dialog.show();
}

function open_letter_dialog(list) {
	const doc = list.frm.doc;
	const url = `/printview?doctype=${encodeURIComponent(
		"Appointment Letter",
	)}&name=${encodeURIComponent(get_letter(list))}&trigger_print=0`;
	const recipient = doc.company_email || doc.personal_email || __("the new hire");

	const dialog = new frappe.ui.Dialog({
		title: __("Send Appointment Letter"),
		size: "large",
		fields: [{ fieldtype: "HTML", fieldname: "preview" }],
		primary_action_label: __("Send"),
		primary_action: async () => {
			await list.call("send_appointment_letter", {}, __("Sending the letter"));
			dialog.hide();
		},
	});
	dialog.fields_dict.preview.$wrapper.append(
		$("<p class='text-ink-gray-6'></p>").text(__("Emails the letter to {0}.", [recipient])),
		$('<iframe class="epc-letter-preview"></iframe>').attr({
			src: url,
			title: __("Appointment letter preview"),
		}),
	);
	dialog.show();
}

async function create_appointment_letter(list) {
	await list.save_if_dirty();
	const doc = list.frm.doc;
	frappe.new_doc("Appointment Letter", {
		job_applicant: doc.job_applicant,
		applicant_name: doc.employee_name,
		company: doc.company,
		appointment_date: doc.date_of_joining,
		employee_preboarding: doc.name,
	});
}

async function create_employee(list) {
	await list.save_if_dirty();
	const doc = await frappe.xcall(
		"hrms.hr.doctype.employee_preboarding.employee_preboarding.make_employee",
		{ source_name: list.frm.doc.name },
	);
	const [employee] = frappe.model.sync(doc);
	frappe.ui.form.make_quick_entry("Employee", () => list.frm.reload_doc(), null, employee, true);
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
		on_created: () => frappe.after_ajax(() => list.call("sync_activities")),
	});
}
