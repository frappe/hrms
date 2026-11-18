const MAIL_API = "frappe.core.doctype.communication.email.make";

// Unsent text, kept per applicant so a refresh or a trip to another applicant doesn't lose it.
const reply_drafts = new Map();

let templates_promise = null;

/** Email templates for applicants (or for any doctype), fetched once per page load. */
function get_templates() {
	templates_promise ||= frappe.db
		.get_list("Email Template", {
			or_filters: [
				["reference_doctype", "=", "Job Applicant"],
				["reference_doctype", "is", "not set"],
			],
			order_by: "name asc",
			limit: 50,
		})
		.then((rows) => rows.map((row) => row.name))
		.catch((error) => {
			templates_promise = null;
			throw error;
		});
	return templates_promise;
}

function escape_to_html(text) {
	return frappe.utils.escape_html(text).replace(/\n/g, "<br>");
}

function get_reply_subject(subject) {
	return /^\s*re\s*:/i.test(subject || "") ? subject : __("Re: {0}", [subject || ""]);
}

function make_icon(name) {
	return $(`<span class="hiring__mail-icon"></span>`).html(
		frappe.utils.icon(name, "sm", "", "", "", true),
	);
}

/** The "Email | Comments" section of the applicant panel: what the candidate reads, and what only the team reads. */
hrms.hiring.ApplicantMail = class ApplicantMail {
	static create_state(data) {
		const can_email = frappe.model.can_email("Job Applicant");
		const unread = data.emails.filter(
			(email) => !email.seen && email.sent_or_received === "Received",
		);
		return {
			tab: can_email ? "email" : "comments",
			unread: new Set(unread.map((email) => email.name)),
			open: new Map(),
			envelopes: new Set(),
			show_earlier: false,
			marked_seen: false,
		};
	}

	/** `reload` refreshes the whole panel, which keeps its scroll position. */
	constructor({ data, state, reload }) {
		this.data = data;
		this.state = state;
		this.reload = reload;
		this.can_email = frappe.model.can_email("Job Applicant");
		this.$content = $(`<div class="hiring__mail-content"></div>`);
		this.$aside = $(`<div class="hiring__mail-aside"></div>`);
		this.$el = $(`<section class="hiring__panel-section hiring__mail"></section>`).append(
			$(`<div class="hiring__mail-head"></div>`).append(this.make_tabs().$el, this.$aside),
			this.$content,
		);
		this.render_tab();
	}

	has_unread() {
		return this.data.emails.some(
			(email) => !email.seen && email.sent_or_received === "Received",
		);
	}

	make_tabs() {
		const { emails, comments } = this.data;
		const suffix = (count, with_dot) => () => {
			const $suffix = $(`<span class="hiring__mail-tab-extra"></span>`);
			if (count)
				$suffix.append($(`<span class="hiring__mail-count text-sm"></span>`).text(count));
			if (with_dot && this.can_email && this.has_unread()) {
				$suffix.append(
					$(`<span class="hiring__mail-dot"></span>`).attr("title", __("Unread")),
				);
			}
			return $suffix;
		};
		this.tabs = new frappe.ui.TabButtons({
			label: __("Email or comments"),
			value: this.state.tab,
			options: [
				{ label: __("Email"), value: "email", suffix: suffix(emails.length, true) },
				{
					label: __("Comments"),
					value: "comments",
					suffix: suffix(comments.length, false),
				},
			],
			on_change: (tab) => {
				this.state.tab = tab;
				this.render_tab();
			},
		});
		// A clicked tab lets go of focus, so the page's arrow shortcuts keep stepping
		// through applicants and stages. Keyboard users who Tab in keep the arrows.
		this.tabs.$el.on("click", () => document.activeElement?.blur());
		return this.tabs;
	}

	render_tab() {
		const is_email = this.state.tab === "email";
		hrms.hiring
			.clear(this.$aside)
			.append(is_email ? this.make_new_email_button() : this.make_team_only());
		hrms.hiring
			.clear(this.$content)
			.append(
				is_email
					? this.make_email_tab()
					: new hrms.hiring.ApplicantComments({ data: this.data, reload: this.reload })
							.nodes,
			);
		if (is_email) this.mark_seen();
	}

	make_team_only() {
		return $(`<span class="hiring__mail-team-only text-p-sm"></span>`).append(
			make_icon("users"),
			$("<span></span>").text(__("Team only")),
		);
	}

	make_new_email_button() {
		if (!this.can_email || !this.data.emails.length || !this.data.can_send_email) return null;
		return frappe.ui.button({
			label: __("New email"),
			icon: "pencil",
			variant: "ghost",
			onclick: () => this.open_composer(),
		});
	}

	/** Reading the thread is what marks it seen; the "New" markers stay for this visit. */
	mark_seen() {
		if (!this.can_email || this.state.marked_seen || !this.has_unread()) return;
		this.state.marked_seen = true;
		frappe
			.xcall(`${APPLICANT_API}.mark_emails_seen`, { job_applicant: this.data.name })
			.then(() => {
				this.data.emails.forEach((email) => (email.seen = 1));
				this.tabs.$el.find(".hiring__mail-dot").remove();
			})
			.catch(() => (this.state.marked_seen = false));
	}

	// Email

	make_email_tab() {
		const { emails } = this.data;
		if (!emails.length) return this.make_empty_thread();
		const thread = new hrms.hiring.ApplicantThread({
			data: this.data,
			state: this.state,
			can_reply: this.can_reply(),
			on_reply: (email) => this.open_composer(email),
		});
		return [thread.$thread, this.make_footer()];
	}

	/** No thread yet: the box for the first email, like the comment box (no empty state). */
	make_empty_thread() {
		const first_name = this.get_first_name();
		// nothing to send with: the setup prompt stands where the box would be
		if (this.can_email && !this.data.can_send_email) {
			return this.make_setup_prompt(__("Email {0} from here", [first_name]));
		}
		if (!this.can_email) return this.make_footer(true);
		return this.make_new_email_box();
	}

	make_new_email_box() {
		const { job_title } = this.data;
		const $subject = $(
			`<input type="text" class="hiring__composer-subject text-p-base-medium">`,
		).attr({
			placeholder: __("Subject"),
			"aria-label": __("Subject"),
			value: job_title ? __("Your application for {0}", [job_title]) : "",
		});
		const composer = this.make_letter({
			placeholder: __("Email {0}", [this.get_first_name()]),
			label: __("Email"),
			$subject,
			on_submit: (text) => this.send_new_email($subject.val(), text),
			apply_template: (template) => {
				if (template.subject) $subject.val(template.subject);
				composer.set_value(template.text);
			},
			open_full_editor: () =>
				this.open_composer(
					null,
					escape_to_html(composer.get_value().trim()),
					$subject.val(),
				),
		});
		return composer.$el;
	}

	send_new_email(subject, text) {
		if (!text.trim()) return Promise.resolve();
		if (!subject.trim()) {
			frappe.ui.toast({ message: __("Add a subject") });
			return Promise.resolve();
		}
		return this.send({ text, subject: subject.trim() });
	}

	/** Emails the applicant `text` (plain, escaped here), then drops the draft and reloads. */
	send({ text, ...args }) {
		const { name, applicant_name, email_id, email_sender } = this.data;
		return frappe
			.xcall(MAIL_API, {
				doctype: "Job Applicant",
				name,
				content: escape_to_html(text.trim()),
				recipients: email_id,
				send_email: 1,
				sender: email_sender,
				...args,
			})
			.then(() => {
				reply_drafts.delete(name);
				frappe.ui.toast({ message: __("Email sent to {0}", [applicant_name]) });
				this.reload();
			});
	}

	get_first_name() {
		return hrms.hiring.get_first_name(this.data.applicant_name);
	}

	/** Under the thread: the reply box, a notice when nothing can be sent, or a hint for users who can't email. */
	make_footer(is_empty) {
		const { can_send_email } = this.data;
		if (!this.can_email) {
			return $(`<p class="hiring__mail-hint text-p-sm"></p>`).append(
				make_icon("lock"),
				$("<span></span>").text(__("Recruiters email candidates")),
			);
		}
		if (!can_send_email)
			return this.make_setup_prompt(__("Reply to {0} from here", [this.get_first_name()]));
		return is_empty ? null : this.make_reply_box();
	}

	/** Where sending would be: the same empty-state shape, dashed, with the setup step. */
	make_setup_prompt(title) {
		const can_set_up = this.data.can_set_up_email;
		return frappe.ui.empty_state({
			icon: "mail-plus",
			title,
			description: can_set_up
				? __("Connect the hiring inbox to send emails and get replies here.")
				: __("Ask your admin to connect the hiring inbox."),
			css_class: "hiring__mail-empty hiring__mail-setup",
			actions: can_set_up
				? [{ label: __("Set up email"), onclick: () => frappe.new_doc("Email Account") }]
				: [],
		});
	}

	can_reply() {
		return this.can_email && this.data.can_send_email;
	}

	// Reply

	make_reply_box() {
		const subject = get_reply_subject(this.get_latest_email().subject);
		const $subject = $(`<span class="hiring__letter-subject-text text-p-base"></span>`).text(
			subject,
		);
		frappe.ui.tooltip($subject, { only_on_overflow: true, side: "bottom" });
		const composer = this.make_letter({
			placeholder: __("Reply to {0}", [this.get_first_name()]),
			label: __("Reply"),
			$subject,
			on_submit: (text) => this.send_reply(text),
			// a reply keeps the thread's subject, so only the template's text is used
			apply_template: (template) => composer.set_value(template.text),
			open_full_editor: () =>
				this.open_composer(
					this.get_latest_email(),
					escape_to_html(composer.get_value().trim()),
				),
		});
		return composer.$el.addClass("hiring__mail-reply");
	}

	/** The email composer as a letter: To, subject, body and footer, resting as one line until opened. */
	make_letter({ placeholder, label, $subject, on_submit, apply_template, open_full_editor }) {
		const { name, applicant_name, email_id, email_sender } = this.data;
		return hrms.hiring.make_composer({
			placeholder,
			label,
			rows: 3,
			drafts: reply_drafts,
			draft_key: name,
			submit: {
				label: __("Send email"),
				icon: "send",
				variant: "solid",
				tooltip: {
					text: __("Send email"),
					shortcut: [is_mac_platform() ? "⌘" : "Ctrl", "↵"],
					side: "top",
				},
			},
			on_submit,
			letter: {
				to_name: applicant_name,
				to_address: email_id,
				$subject,
				from: $(`<span class="hiring__composer-from text-p-sm"></span>`).text(
					__("From {0}", [email_sender]),
				),
				tools: [
					this.make_template_button(apply_template),
					this.make_full_editor_menu(open_full_editor),
				],
			},
		});
	}

	get_latest_email() {
		return this.data.emails[this.data.emails.length - 1];
	}

	send_reply(text) {
		if (!text.trim()) return Promise.resolve();
		const latest = this.get_latest_email();
		return this.send({
			text,
			subject: get_reply_subject(latest.subject),
			in_reply_to: latest.name,
		});
	}

	/** Lists the applicant's email templates; picking one renders it for this applicant and hands it to `apply`. */
	make_template_button(apply) {
		return frappe.ui.dropdown({
			button: {
				label: __("Template"),
				icon: "file-text",
				variant: "ghost",
				size: "sm",
				css_class: "hiring__letter-template",
				tooltip: __("Template"),
			},
			empty_text: __("No email templates for applicants"),
			options: () =>
				get_templates().then((names) =>
					names.map((template_name) => ({
						label: template_name,
						onclick: () =>
							hrms.hiring.render_template(template_name, this.data).then(apply),
					})),
				),
		});
	}

	make_full_editor_menu(open) {
		return frappe.ui.dropdown({
			button: { icon: "ellipsis", variant: "ghost", size: "sm", tooltip: __("More") },
			align: "end",
			options: [{ label: __("Open full editor"), icon: "maximize-2", onclick: open }],
		});
	}

	/** The full composer: a new mail, or a reply to `reply_to` with `content` already in it. */
	async open_composer(reply_to, content, subject) {
		const { name, email_id, email_sender } = this.data;
		// the whole document, so a template renders with the applicant's fields
		const doc = await frappe.db.get_doc("Job Applicant", name);
		new frappe.views.CommunicationComposer({
			doc,
			recipients: email_id,
			sender: email_sender,
			subject: reply_to ? get_reply_subject(reply_to.subject) : subject || "",
			is_a_reply: Boolean(reply_to),
			last_email: reply_to,
			message: content,
			success: () => {
				reply_drafts.delete(name);
				this.reload();
			},
		});
	}
};
