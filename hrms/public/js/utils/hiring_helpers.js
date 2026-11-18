frappe.provide("hrms.hiring");

const TEMPLATE_API = "frappe.email.doctype.email_template.email_template.get_email_template";

hrms.hiring.html_to_text = (html) => {
	const spaced = (html || "").replace(/<(br|\/p|\/div|\/li|\/h\d)\s*\/?>/gi, "\n");
	return frappe.utils
		.html2text(spaced)
		.replace(/\n{3,}/g, "\n\n")
		.trim();
};

hrms.hiring.get_first_name = (applicant_name) => (applicant_name || "").trim().split(/\s+/)[0];

/** Renders an email template for the applicant `{name, email_sender}`; resolves {subject, text}. */
hrms.hiring.render_template = async (template_name, { name, email_sender }) => {
	const doc = await frappe.db.get_doc("Job Applicant", name);
	const { subject, message } = await frappe.xcall(TEMPLATE_API, {
		template_name,
		doc,
		sender: email_sender,
	});
	return { subject, text: hrms.hiring.html_to_text(message) };
};

/**
 * A small confirm dialog with an HTML `body` (escape record text in it and in `title`).
 * `on_confirm` may return a promise; the dialog closes once it resolves and stays open if it fails.
 */
hrms.hiring.open_confirm_dialog = ({
	title,
	body,
	primary_label,
	theme,
	secondary_label,
	on_confirm,
}) => {
	const dialog = new frappe.ui.Dialog({
		title,
		fields: [{ fieldname: "body", fieldtype: "HTML", options: body }],
		primary_action_label: primary_label,
		primary_action: async () => {
			dialog.disable_primary_action();
			try {
				await on_confirm();
				dialog.hide();
			} catch (error) {
				dialog.enable_primary_action();
				throw error;
			}
		},
		secondary_action_label: secondary_label || __("Cancel"),
		secondary_action: () => dialog.hide(),
	});
	frappe.ui.button.dress(dialog.get_primary_btn(), {
		label: primary_label,
		variant: "solid",
		theme: theme || "gray",
	});
	dialog.show();
	return dialog;
};

/** Stage colours, shared by the applicant form pill and the applicant list. */
hrms.hiring.STAGE_THEMES = {
	Applied: "gray",
	Shortlisted: "blue",
	Interviewing: "amber",
	Offered: "purple",
	Hired: "green",
	Rejected: "red",
};

/** The stage badge `{label, theme}` of an applicant; an applicant on hold reads "On hold". */
hrms.hiring.get_stage_badge = ({ stage, status }) =>
	status === "Hold"
		? { label: __("On hold"), theme: "gray" }
		: { label: __(stage), theme: hrms.hiring.STAGE_THEMES[stage] || "gray" };

hrms.hiring.INTERVIEW_BADGE_THEMES = {
	Pending: "gray",
	"Under Review": "amber",
	Cleared: "green",
	Rejected: "red",
	Cancelled: "gray",
};

hrms.hiring.get_interview_status_label = (status) =>
	status === "Under Review" ? __("Under review") : __(status);

/** The badge `{label, theme}` of an interview; feedback that all rejects reads as "Not cleared" while the status is still open. */
hrms.hiring.get_interview_badge = ({ status, is_not_cleared }) => {
	if (is_not_cleared && ["Pending", "Under Review"].includes(status)) {
		return { label: __("Not cleared"), theme: "red" };
	}
	return {
		label: hrms.hiring.get_interview_status_label(status),
		theme: hrms.hiring.INTERVIEW_BADGE_THEMES[status],
	};
};

hrms.hiring.OFFER_BADGE_THEMES = {
	"Ready to Send": "blue",
	"Awaiting Response": "amber",
	Accepted: "green",
	Rejected: "red",
};

/** The badge `{label, theme}` of a job offer status; a stored "Rejected" reads "Declined", as the candidate declined. */
hrms.hiring.get_offer_badge = (status) => {
	const labels = {
		"Ready to Send": __("Ready to send"),
		"Awaiting Response": __("Sent"),
		Rejected: __("Declined"),
	};
	return { label: labels[status] || __(status), theme: hrms.hiring.OFFER_BADGE_THEMES[status] };
};

hrms.hiring.CLOSING_SOON_DAYS = 7;

/** "Closes today", "Closes tomorrow" or "Closes in 3 days", for an opening closing `days` from today. */
hrms.hiring.get_closing_label = (days) => {
	if (days === 0) return __("Closes today");
	if (days === 1) return __("Closes tomorrow");
	return __("Closes in {0} days", [days]);
};

/** The Hiring page route of an opening, at a stage and an applicant when given; the URL spells the stage lowercase. */
hrms.hiring.get_pipeline_route = (opening, stage, applicant) =>
	["hiring", opening, stage?.toLowerCase(), applicant].filter(Boolean);

/** A DOM element for the Custom HTML Blocks: `text` sets its text, other attributes are set as given. */
hrms.hiring.make_element = (tag, attrs = {}, ...children) => {
	const node = document.createElement(tag);
	for (const [key, value] of Object.entries(attrs)) {
		if (value === undefined || value === null || value === false) continue;
		if (key === "text") node.textContent = value;
		else node.setAttribute(key, value === true ? "" : value);
	}
	node.append(...children.filter(Boolean));
	return node;
};

/**
 * The desk router only sees clicks in the light DOM, so a block routes the /desk/ links inside its
 * shadow root. `handle_link(link)` may take a link over by returning true.
 */
hrms.hiring.route_block_links = (root_element, handle_link) => {
	root_element.addEventListener("click", (event) => {
		const link = event.target.closest?.("a[href^='/desk/']");
		if (
			!link ||
			event.button !== 0 ||
			event.ctrlKey ||
			event.metaKey ||
			event.shiftKey ||
			event.altKey
		)
			return;
		event.preventDefault();
		if (!handle_link?.(link)) frappe.set_route(link.getAttribute("href"));
	});
};

/** Hides a block on the workspace; it stays while the workspace is edited so it can still be moved. */
hrms.hiring.hide_block = (root_element) => {
	if (!root_element.host.closest(".edit-mode"))
		root_element.host.closest(".ce-block")?.setAttribute("hidden", "");
};
