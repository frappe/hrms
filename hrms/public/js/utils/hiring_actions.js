frappe.provide("hrms.hiring");

/**
 * The steps that move an applicant through the pipeline, shared by the Hiring page and the
 * Job Applicant Kanban. Each one takes {name, applicant_name, ...} and returns a promise that
 * resolves true once the step is done and false when it is cancelled.
 */

const APPLICANT_API = "hrms.hr.page.hiring.applicant";

/** Resolves true once an interview is booked (and says so in a toast), false when cancelled. */
hrms.hiring.schedule_interview = async (applicant) => {
	const designation =
		applicant.designation ??
		(await frappe.db.get_value("Job Applicant", applicant.name, "designation"))?.message
			?.designation;
	const is_scheduled = await new Promise((resolve) =>
		hrms.schedule_interview({
			job_applicant: applicant.name,
			designation,
			on_scheduled: () => resolve(true),
			on_cancel: () => resolve(false),
		}),
	);
	if (is_scheduled)
		frappe.ui.toast({
			message: __("Interview scheduled for {0}", [applicant.applicant_name]),
		});
	return is_scheduled;
};

/**
 * Rejects with a dialog asking for the reason and offering to email the applicant.
 * Resolves {previous_status, communication, emailed} once rejected, false when cancelled.
 */
hrms.hiring.reject = async (applicant) => {
	const send = (values = {}) =>
		frappe.xcall(`${APPLICANT_API}.reject_applicant`, {
			job_applicant: applicant.name,
			reason: values.reason,
			note: values.note,
			send_email: values.send_email ? 1 : 0,
			subject: values.send_email ? values.subject : null,
			message: values.send_email ? values.message : null,
		});
	const done = (rejection, emailed) => ({ ...rejection, emailed });

	// the reason is asked for every time; the email options only show when mail can go out
	const details = applicant.reject_details || (await get_reject_details(applicant.name));
	const can_email = frappe.model.can_email("Job Applicant") && Boolean(details.can_send_email);

	return new Promise((resolve) => {
		let is_rejected = false;
		hrms.hiring
			.open_reject_dialog({
				applicant: details,
				can_email,
				on_reject: async (values) => {
					const rejection = await send(values);
					is_rejected = true;
					resolve(done(rejection, can_email && Boolean(values.send_email)));
				},
				on_cancel: () => !is_rejected && resolve(false),
			})
			.catch(() => resolve(false));
	});
};

/** The toast after a reject, with the Undo that restores the status, the interviews and cancels the email. */
hrms.hiring.show_reject_toast = ({ applicant, rejection, on_undo }) => {
	const message = rejection.emailed
		? __("{0} rejected. Rejection email queued.", [applicant.applicant_name])
		: __("{0} rejected", [applicant.applicant_name]);
	const toast = frappe.ui.toast({
		message,
		action: {
			label: __("Undo"),
			onclick: async () => {
				toast.dismiss();
				await hrms.hiring.undo_reject(applicant.name, rejection.previous_status, {
					communication: rejection.communication,
					closed_interviews: rejection.closed_interviews,
					first_name: hrms.hiring.get_first_name(applicant.applicant_name),
				});
				on_undo?.();
			},
		},
	});
	return toast;
};

hrms.hiring.undo_reject = async (
	name,
	previous_status,
	{ communication, closed_interviews, first_name },
) => {
	const { email_cancelled } = await frappe.xcall(`${APPLICANT_API}.undo_reject_applicant`, {
		job_applicant: name,
		previous_status,
		communication,
		closed_interviews: JSON.stringify(closed_interviews || []),
	});
	if (communication && !email_cancelled) {
		frappe.ui.toast({ message: __("Email already sent to {0}", [first_name]) });
	}
};

async function get_reject_details(job_applicant) {
	return frappe.xcall(`${APPLICANT_API}.get_reject_details`, { job_applicant }, "GET");
}

/**
 * One rule for "ready for an offer", used by every path that makes an offer: an applicant with a
 * cleared interview, or with no interviews at all, goes straight on; one interviewed without a
 * cleared result is asked first. Resolves true to go on.
 */
hrms.hiring.confirm_offer = async (applicant) => {
	const { needs_confirmation } = await hrms.hiring.get_offer_readiness(applicant.name);
	if (!needs_confirmation) return true;
	return new Promise((resolve) =>
		frappe.confirm(
			__("{0} has no cleared interview yet. Create an offer anyway?", [
				frappe.utils.escape_html(applicant.applicant_name || applicant.name),
			]),
			() => resolve(true),
			() => resolve(false),
		),
	);
};

hrms.hiring.get_offer_readiness = (job_applicant) =>
	frappe.xcall(`${APPLICANT_API}.get_offer_readiness`, { job_applicant }, "GET");

/**
 * Opens a new Job Offer. Interviews that have a result but are still drafts are submitted
 * first, after a confirmation: an offer follows decided interviews.
 */
hrms.hiring.create_offer = async (applicant) => {
	const job_applicant = applicant.name;
	if (!(await hrms.hiring.confirm_offer(applicant))) return false;
	const drafts = await get_decided_drafts(job_applicant);
	const open_offer = async () => {
		const { designation, company } = await get_offer_defaults(applicant);
		frappe.new_doc("Job Offer", {
			job_applicant,
			applicant_name: applicant.applicant_name,
			designation,
			company,
		});
		return true;
	};
	if (!drafts.length) return open_offer();

	return new Promise((resolve) => {
		let is_confirmed = false;
		open_submit_results_dialog({
			drafts,
			on_confirm: async () => {
				await frappe.xcall(`${APPLICANT_API}.submit_interview_results`, { job_applicant });
				is_confirmed = true;
				resolve(await open_offer());
			},
			on_cancel: () => !is_confirmed && resolve(false),
		});
	});
};

async function get_offer_defaults({ name, designation, company }) {
	if (designation && company) return { designation, company };
	const { message: applicant } = await frappe.db.get_value("Job Applicant", name, [
		"designation",
		"job_title",
	]);
	const opening = await frappe.db.get_value("Job Opening", applicant?.job_title, ["company"]);
	return {
		designation: designation ?? applicant?.designation,
		company: company ?? opening?.message?.company,
	};
}

async function get_decided_drafts(job_applicant) {
	try {
		return await frappe.db.get_list("Interview", {
			filters: { job_applicant, docstatus: 0, status: ["in", ["Cleared", "Rejected"]] },
			fields: ["name", "interview_type", "status"],
			order_by: "scheduled_on asc, creation asc",
			limit: 0,
		});
	} catch {
		return [];
	}
}

const RESULT_BADGE_THEMES = { Cleared: "green", Rejected: "red" };

function open_submit_results_dialog({ drafts, on_confirm, on_cancel }) {
	const list = new frappe.ui.ItemList({
		variant: "flat",
		items: drafts.map(({ name, interview_type, status }) => ({
			id: name,
			title: interview_type,
			badge: { label: __(status), theme: RESULT_BADGE_THEMES[status] },
		})),
	});
	const note = frappe.utils.escape_html(__("Submitted interviews can't be edited."));
	const dialog = hrms.hiring.open_confirm_dialog({
		title:
			drafts.length === 1
				? __("Submit the interview result first?")
				: __("Submit {0} interview results first?", [drafts.length]),
		body: `<p class="hiring__dialog-note text-p-sm">${note}</p>`,
		primary_label: __("Submit and create offer"),
		on_confirm,
	});
	dialog.fields_dict.body.$wrapper.prepend(list.$el);
	dialog.onhide = () => on_cancel?.();
}

/**
 * The rule for moving an applicant to a stage, shared by the Kanban drop and the form's Stage
 * field. Runs the step the stage needs and resolves "move" (plain change), "done" (the step
 * did the move) or "cancel".
 */
hrms.hiring.move_to_stage = async (applicant, to, { on_undo } = {}) => {
	const name = applicant.name;
	let is_done;
	switch (to) {
		case "Interviewing":
			is_done = await hrms.hiring.schedule_interview(applicant);
			break;
		case "Rejected": {
			const rejection = await hrms.hiring.reject(applicant);
			is_done = Boolean(rejection);
			if (is_done) {
				hrms.hiring.show_reject_toast({
					applicant,
					rejection,
					on_undo,
				});
			}
			break;
		}
		case "Offered": {
			const readiness = await hrms.hiring.get_offer_readiness(name);
			if (readiness.has_live_offer) {
				frappe.msgprint(
					__("{0} already has an offer.", [
						frappe.utils.escape_html(applicant.applicant_name),
					]),
				);
				return "cancel";
			}
			is_done = await hrms.hiring.create_offer(applicant);
			break;
		}
		case "Hired": {
			// never opens a form: Hired follows an accepted offer
			const readiness = await hrms.hiring.get_offer_readiness(name);
			if (readiness.has_accepted_offer) return "move";
			const applicant_name = frappe.utils.escape_html(applicant.applicant_name);
			frappe.msgprint(
				readiness.has_live_offer
					? __("Mark {0}'s offer as accepted first.", [applicant_name])
					: __("{0} has no offer yet. Create an offer first.", [applicant_name]),
			);
			return "cancel";
		}
		default:
			return "move";
	}
	return is_done ? "done" : "cancel";
};
