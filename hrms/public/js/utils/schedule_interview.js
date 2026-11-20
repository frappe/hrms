frappe.provide("hrms");

/** Who can be picked as an interviewer: real, enabled desk users. */
hrms.interviewer_filters = () => ({
	enabled: 1,
	user_type: "System User",
	name: ["not in", ["Guest", "Administrator"]],
});

/** Shows full names instead of user IDs in the pills of an interviewers field. */
hrms.show_interviewer_names = async (control, ids) => {
	ids = ids || [];
	await Promise.all(
		ids
			.filter((id) => !frappe.utils.get_link_title("User", id))
			.map(async (id) => {
				const { message } = await frappe.db.get_value("User", id, "full_name");
				if (message?.full_name) frappe.utils.add_link_title("User", id, message.full_name);
			}),
	);
	control?.set_pill_html?.(ids);
};

const TIME_FORMAT = "HH:mm:ss";
const DEFAULT_DURATION_MINUTES = 30;

/** "28 Oct · 3:00 PM": how an interview's date and start time read in the Hiring pipeline and its toasts. */
hrms.format_interview_time = (date, from_time) =>
	[moment(date).format("D MMM"), from_time && moment(from_time, TIME_FORMAT).format("LT")]
		.filter(Boolean)
		.join(" · ");

const END_BEFORE_START = () => __("End time must be after start time");

function is_end_after_start(from_time, to_time) {
	if (!from_time || !to_time) return true;
	return moment(to_time, TIME_FORMAT).isAfter(moment(from_time, TIME_FORMAT));
}

/**
 * Returns the From Time field's onchange: To Time follows the start, keeping the length it had
 * (30 minutes when there was none). `start` is the From Time the dialog begins with, if any.
 */
function make_follow_start(dialog, start) {
	let previous_from = start || null;
	return () => {
		const from_time = dialog.get_value("from_time");
		const to_time = dialog.get_value("to_time");
		if (from_time && from_time !== previous_from) {
			const gap =
				previous_from && to_time
					? moment(to_time, TIME_FORMAT).diff(
							moment(previous_from, TIME_FORMAT),
							"minutes",
					  )
					: 0;
			const start_at = moment(from_time, TIME_FORMAT);
			const end = start_at.clone().add(gap > 0 ? gap : DEFAULT_DURATION_MINUTES, "minutes");
			// past midnight there is no valid end the time fields can hold
			if (end.isSame(start_at, "day") && (previous_from || !to_time)) {
				dialog.set_value("to_time", end.format(TIME_FORMAT));
			}
		}
		previous_from = from_time || null;
	};
}

/**
 * Asks for the interview details and schedules an Interview for the applicant.
 * @param {{job_applicant: string, designation?: string, on_scheduled?: (interview: string) => void, on_cancel?: () => void}} opts
 */
hrms.schedule_interview = ({ job_applicant, designation, on_scheduled, on_cancel }) => {
	frappe.model.with_doctype("Interview Detail", () =>
		show_schedule_interview_dialog({ job_applicant, designation, on_scheduled, on_cancel }),
	);
};

function show_schedule_interview_dialog({ job_applicant, designation, on_scheduled, on_cancel }) {
	let is_scheduled = false;
	let is_scheduling = false;
	let follow_start = () => {};
	const dialog = new frappe.ui.Dialog({
		title: __("Schedule Interview"),
		fields: [
			{
				label: __("Interview Type"),
				fieldname: "interview_type",
				fieldtype: "Link",
				options: "Interview Type",
				reqd: 1,
				get_query: () => ({
					filters: designation ? [["designation", "in", [designation, ""]]] : [],
				}),
				onchange() {
					const interview_type = dialog.get_value("interview_type");
					if (!interview_type) return;
					frappe.call({
						method: "hrms.hr.doctype.interview.interview.get_interviewers",
						args: { interview_type },
						callback(r) {
							dialog.set_value(
								"interviewers",
								(r.message || []).map((i) => ({ interviewer: i.interviewer })),
							);
						},
					});
				},
			},
			{
				label: __("Scheduled On"),
				fieldname: "scheduled_on",
				fieldtype: "Date",
				reqd: 1,
				default: frappe.datetime.get_today(),
			},
			{ fieldtype: "Column Break" },
			{
				label: __("From Time"),
				fieldname: "from_time",
				fieldtype: "Time",
				reqd: 1,
				onchange: () => follow_start(),
			},
			{
				label: __("To Time"),
				fieldname: "to_time",
				fieldtype: "Time",
				reqd: 1,
				onchange: () => dialog.fields_dict.error.$wrapper.empty(),
			},
			{ fieldtype: "Section Break", label: __("Interviewers") },
			{
				fieldname: "interviewers",
				fieldtype: "Table MultiSelect",
				options: "Interview Detail",
				get_query: () => ({ filters: hrms.interviewer_filters() }),
				onchange() {
					const ids = (dialog.get_value("interviewers") || []).map((i) => i.interviewer);
					hrms.show_interviewer_names(dialog.fields_dict.interviewers, ids);
					dialog.fields_dict.error.$wrapper.empty();
				},
			},
			{ fieldname: "error", fieldtype: "HTML" },
		],
		primary_action_label: __("Schedule"),
		primary_action(values) {
			const show_error = (message) =>
				dialog.fields_dict.error.$wrapper.html(
					`<p class="text-danger small">${frappe.utils.escape_html(message)}</p>`,
				);
			if (!(values.interviewers || []).some((i) => i.interviewer)) {
				return show_error(__("Add at least one interviewer"));
			}
			if (!is_end_after_start(values.from_time, values.to_time))
				return show_error(END_BEFORE_START());
			if (is_scheduling) return;
			const start = moment(`${values.scheduled_on} ${values.from_time || "00:00:00"}`);
			if (start.isBefore(moment())) {
				frappe.confirm(__("This time has already passed. Schedule it anyway?"), () =>
					schedule(values),
				);
				return;
			}
			schedule(values);
		},
	});
	follow_start = make_follow_start(dialog);
	const schedule = (values) => {
		if (is_scheduling) return;
		is_scheduling = true;
		dialog.disable_primary_action();
		frappe.call({
			method: "hrms.hr.doctype.job_applicant.job_applicant.schedule_interview",
			args: {
				job_applicant,
				interview_type: values.interview_type,
				scheduled_on: values.scheduled_on,
				from_time: values.from_time || null,
				to_time: values.to_time || null,
				interviewers: values.interviewers || [],
			},
			error() {
				is_scheduling = false;
				dialog.enable_primary_action();
			},
			callback(r) {
				if (!r.message) {
					is_scheduling = false;
					dialog.enable_primary_action();
					return;
				}
				is_scheduled = true;
				dialog.hide();
				on_scheduled?.(r.message);
			},
		});
	};
	dialog.onhide = () => {
		if (!is_scheduled) on_cancel?.();
	};
	dialog.show();
}

/**
 * Asks for a new date and time and moves the interview. Shared by the Interview form and the
 * Hiring pipeline. `interview` needs name, scheduled_on, from_time and to_time.
 * @param {{interview: {name: string, scheduled_on: string, from_time: string, to_time: string}, on_rescheduled?: () => void}} opts
 */
hrms.reschedule_interview = ({ interview, on_rescheduled }) => {
	let follow_start = () => {};
	const dialog = new frappe.ui.Dialog({
		title: __("Reschedule Interview"),
		fields: [
			{
				label: __("Scheduled On"),
				fieldname: "scheduled_on",
				fieldtype: "Date",
				reqd: 1,
				default: interview.scheduled_on,
			},
			{
				label: __("From Time"),
				fieldname: "from_time",
				fieldtype: "Time",
				reqd: 1,
				default: interview.from_time,
				onchange: () => follow_start(),
			},
			{
				label: __("To Time"),
				fieldname: "to_time",
				fieldtype: "Time",
				reqd: 1,
				default: interview.to_time,
				onchange: () => dialog.fields_dict.error.$wrapper.empty(),
			},
			{ fieldname: "error", fieldtype: "HTML" },
		],
		primary_action_label: __("Reschedule"),
		async primary_action(values) {
			if (!is_end_after_start(values.from_time, values.to_time)) {
				dialog.fields_dict.error.$wrapper.html(
					`<p class="text-danger small">${frappe.utils.escape_html(
						END_BEFORE_START(),
					)}</p>`,
				);
				return;
			}
			dialog.disable_primary_action();
			let response;
			try {
				response = await frappe.call({
					method: "run_doc_method",
					args: {
						dt: "Interview",
						dn: interview.name,
						method: "reschedule_interview",
						args: {
							scheduled_on: values.scheduled_on,
							from_time: values.from_time,
							to_time: values.to_time,
						},
					},
				});
			} catch (error) {
				dialog.enable_primary_action();
				throw error;
			}
			dialog.hide();
			on_rescheduled?.();
			if (!response.message?.rescheduled) return;
			let message = __("Interview moved to {0}", [
				hrms.format_interview_time(values.scheduled_on, values.from_time),
			]);
			if (!response.message.email_sent) {
				message += " · " + __("No email sent: outgoing email isn't set up");
			}
			frappe.show_alert({ message, indicator: "green" }, 5);
		},
	});
	follow_start = make_follow_start(dialog, interview.from_time);
	dialog.show();
};
