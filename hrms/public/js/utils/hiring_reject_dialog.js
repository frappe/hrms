frappe.provide("hrms.hiring");

const REJECTION_TEMPLATE = "Applicant rejection";

function get_default_rejection({ applicant_name, job_title, company }) {
	const first_name = hrms.hiring.get_first_name(applicant_name);
	// an applicant with no opening has no role or company to name
	if (!job_title || !company) {
		return {
			subject: __("Your application"),
			message: __(
				"Hi {0},\n\nThank you for your interest and for the time you put into applying. After careful review, we've decided not to move forward with your application.\n\nWe appreciate you considering us and wish you the best in your search.\n\nBest regards,\nHiring Team",
				[first_name],
			),
		};
	}
	return {
		subject: __("Your application for {0}", [job_title]),
		message: __(
			"Hi {0},\n\nThank you for your interest in the {1} role at {2} and for the time you put into applying. After careful review, we've decided not to move forward with your application.\n\nWe appreciate you considering us and wish you the best in your search.\n\nBest regards,\n{2} Hiring Team",
			[first_name, job_title, company],
		),
	};
}

/** The name of the rejection email template when the site has one and the user can read it. */
async function find_rejection_template() {
	try {
		return (await frappe.db.exists("Email Template", REJECTION_TEMPLATE))
			? REJECTION_TEMPLATE
			: null;
	} catch {
		return null;
	}
}

/**
 * Asks for the reason (and an optional note), then whether to email the applicant, before rejecting
 * them. `applicant` needs name, applicant_name, job_title, company and email_sender (see
 * get_reject_details); `can_email` false leaves the email options out.
 * `on_reject(values)` returns a promise; the dialog closes when it resolves. `on_cancel` runs on every close.
 */
hrms.hiring.open_reject_dialog = async ({ applicant, can_email = true, on_reject, on_cancel }) => {
	const default_text = get_default_rejection(applicant);
	const first_name = hrms.hiring.get_first_name(applicant.applicant_name);
	const escape = frappe.utils.escape_html;
	const template_name = can_email ? await find_rejection_template() : null;
	let dialog;
	let is_rejecting = false;

	const sync = () => {
		const { reason, send_email, subject, message } = dialog.get_values(true);
		frappe.ui.button.dress(dialog.get_primary_btn(), {
			label: send_email ? __("Reject and email") : __("Reject"),
			variant: "solid",
			theme: "red",
		});
		const is_blank = !(subject || "").trim() || !(message || "").trim();
		dialog
			.get_primary_btn()
			.prop("disabled", is_rejecting || !reason || (Boolean(send_email) && is_blank));
	};

	const fill = ({ subject, message }) => {
		dialog.set_values({ subject, message });
		sync();
	};

	const apply_template = async () => {
		const { subject, text } = await hrms.hiring.render_template(template_name, applicant);
		fill({ subject, message: text });
	};

	dialog = new frappe.ui.Dialog({
		title: __("Reject {0}", [escape(applicant.applicant_name)]),
		fields: [
			{
				fieldname: "reason",
				fieldtype: "Link",
				label: __("Reason"),
				options: "Rejection Reason",
				only_select: true,
				reqd: 1,
				onchange: sync,
			},
			{
				fieldname: "note",
				fieldtype: "Small Text",
				label: __("Note"),
				description: __("Only your team sees this"),
			},
			{
				fieldname: "send_email",
				fieldtype: "Check",
				label: __("Email {0}", [escape(first_name)]),
				default: can_email ? 1 : 0,
				hidden: !can_email,
				onchange: sync,
			},
			{
				fieldname: "sender",
				fieldtype: "HTML",
				depends_on: "send_email",
				options: `<p class="hiring__mail-from">${escape(
					__("From {0}", [applicant.email_sender]),
				)}</p>`,
			},
			{
				fieldname: "subject",
				fieldtype: "Data",
				label: __("Subject"),
				depends_on: "send_email",
			},
			{
				fieldname: "message",
				fieldtype: "Text",
				label: __("Message"),
				depends_on: "send_email",
			},
		],
		primary_action_label: can_email ? __("Reject and email") : __("Reject"),
		primary_action: async (values) => {
			// a repeated click or ⌘↵ must not reject (and email) twice
			is_rejecting = true;
			sync();
			try {
				await on_reject(values);
				dialog.hide();
			} finally {
				is_rejecting = false;
				sync();
			}
		},
	});

	const { subject, message } = dialog.fields_dict;
	message.$input.css("height", "auto").attr("rows", 8);
	for (const field of [subject, message]) field.$input.on("input", sync);
	dialog.fields_dict.note.$input.attr("rows", 2);
	// capture phase: the reason's autocomplete would otherwise take ⌘↵ as picking its first option
	dialog.$wrapper[0].addEventListener(
		"keydown",
		(event) => {
			if (event.key !== "Enter" || !(event.metaKey || event.ctrlKey)) return;
			event.preventDefault();
			event.stopPropagation();
			const $primary = dialog.get_primary_btn();
			if (!$primary.prop("disabled")) $primary.trigger("click");
		},
		true,
	);

	if (template_name) await apply_template();
	else fill(default_text);
	sync();
	dialog.onhide = () => on_cancel?.();
	dialog.show();
};
