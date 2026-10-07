// What each Employee Onboarding Activity action shows and does. An activity record names
// its action; the row's value, lock and buttons come from the handler for that action.

const USER_FIELDS = ["personal_email", "company_email", "create_user_for"];

const EMPLOYEE_FIELDS = [
	"department",
	"designation",
	"employee_grade",
	"branch",
	"employment_type",
	"reports_to",
	"holiday_list",
	"gender",
	"date_of_birth",
];

const ACTION_HANDLERS = {
	"Create User": {
		get_value: (list, row) => row.reference_name,
		get_actions: (list, row, status) =>
			status === "done"
				? [open_action("User", row.reference_name)]
				: [{ label: __("Create"), onclick: () => open_fields_dialog(list, user_dialog) }],
	},
	"Appointment Letter": {
		get_value: (list, row) => {
			const sent_on = list.frm.doc.appointment_letter_sent_on;
			if (sent_on)
				return __("Sent on {0}", [frappe.datetime.str_to_user(sent_on, false, true)]);
			return list.frm.doc.appointment_letter;
		},
		// Appointment Letter still requires a Job Applicant, so an offer without one can't have a letter.
		get_lock_reason: (list) =>
			list.frm.doc.job_applicant ? null : __("Needs a Job Applicant on the Job Offer"),
		get_actions: (list, row, status) => {
			const letter = list.frm.doc.appointment_letter;
			if (status === "done") return [open_action("Appointment Letter", letter)];
			if (!letter)
				return [{ label: __("Create"), onclick: () => create_appointment_letter(list) }];
			return [{ label: __("Send"), icon: "send", onclick: () => open_letter_dialog(list) }];
		},
	},
	"Create Employee": {
		get_value: (list, row) => row.reference_name,
		get_actions: (list, row, status) =>
			status === "done"
				? [open_action("Employee", row.reference_name)]
				: [
						{
							label: __("Create"),
							onclick: () => open_fields_dialog(list, employee_dialog),
						},
				  ],
	},
	Assign: {
		get_value: (list, row) =>
			row.reference_name || list.get_offer_default(row.reference_doctype)?.value,
		get_actions: (list, row, status) => {
			if (row.reference_name)
				return [open_action(row.reference_doctype, row.reference_name)];
			if (status !== "pending") return [];
			return [{ label: __("Assign"), onclick: () => assign(list, row) }];
		},
	},
	Manual: {
		get_value: () => null,
		get_actions: (list, row, status) =>
			status === "pending"
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
	title: __("Create User"),
	fieldnames: USER_FIELDS,
	primary_label: __("Create User"),
	method: "create_user",
	freeze_message: __("Creating the user"),
};

const employee_dialog = {
	title: __("Create Employee"),
	description: __(
		"Check the job details. Personal details come from what the new hire submitted.",
	),
	fieldnames: EMPLOYEE_FIELDS,
	primary_label: __("Create Employee"),
	method: "create_employee",
	freeze_message: __("Creating the employee"),
};

export function get_action_handler(action) {
	return ACTION_HANDLERS[action] || ACTION_HANDLERS.Manual;
}

function open_action(doctype, name) {
	return {
		label: __("Open"),
		variant: "subtle",
		icon_right: "arrow-up-right",
		onclick: () => frappe.set_route("Form", doctype, name),
	};
}

// The onboarding's own fields, edited in a dialog and saved before the action runs.
function open_fields_dialog(
	list,
	{ title, description, fieldnames, primary_label, method, freeze_message },
) {
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
			default: frm.doc[df.fieldname],
		}));
	if (fields.length > 5)
		fields.splice(Math.ceil(fields.length / 2), 0, { fieldtype: "Column Break" });

	const dialog = new frappe.ui.Dialog({
		title,
		fields: description
			? [
					{
						fieldtype: "HTML",
						options: `<p class="text-ink-gray-6">${description}</p>`,
					},
					...fields,
			  ]
			: fields,
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
	)}&name=${encodeURIComponent(doc.appointment_letter)}&trigger_print=0`;
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
		$('<iframe class="eoc-letter-preview"></iframe>').attr({
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
		employee_onboarding: doc.name,
	});
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
		on_created: () => list.call("sync_activities"),
	});
}
