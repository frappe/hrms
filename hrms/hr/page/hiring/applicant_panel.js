const OFFER_BADGE_THEMES = {
	"Ready to Send": "blue",
	"Awaiting Response": "amber",
	Accepted: "green",
	Rejected: "red",
};

function get_offer_status_label({ status }) {
	// the stored status stays "Rejected"; the candidate declined
	const labels = {
		"Ready to Send": __("Ready to send"),
		"Awaiting Response": __("Sent"),
		Rejected: __("Declined"),
	};
	return labels[status] || __(status);
}

function format_short_date(date) {
	return moment(date).format("D MMM");
}

function get_web_url(value) {
	if (!value) return null;
	const url = new URL(value, window.location.origin);
	return ["http:", "https:"].includes(url.protocol) ? url : null;
}

function open_in_new_tab(url) {
	window.open(url.href, "_blank", "noopener");
}

/** A titled section; `actions` are buttons at the right end of the title row. */
function make_section(label, count, content, actions) {
	return $(`<section class="hiring__panel-section"></section>`).append(
		make_heading(label, count, actions),
		...[content].flat(),
	);
}

hrms.hiring.ApplicantPanel = class ApplicantPanel {
	constructor(view) {
		this.view = view;
		this.name = null;
		this.data = null;
		this.loader = new frappe.ui.DetailLoader({
			fetch: (name, { silent }) =>
				frappe
					.call({
						method: `${APPLICANT_API}.get_applicant`,
						type: "GET",
						args: { job_applicant: name },
						silent,
					})
					.then((r) => r.message),
			get_neighbours: (name) => view.pane?.get_neighbour_ids(name) || [],
		});
		this.decisions = new hrms.hiring.ApplicantDecisions(this);
		this.$body = $(`<div class="hiring__panel-body"></div>`);
		this.$scroll = $(`<div class="hiring__panel-scroll"></div>`).append(this.$body);
		this.$bar = $(`<div class="hiring__panel-bar"></div>`).hide();
		this.$el = $(`<aside class="hiring__panel"></aside>`)
			.attr("aria-label", __("Applicant"))
			.append(this.$scroll, this.$bar);
	}

	reset() {
		this.loader.cancel();
		this.cancel_idle_render();
		this.name = null;
		this.data = null;
		this.mail_state = null;
		this.$bar.hide();
		this.show_skeleton();
	}

	clear() {
		this.reset();
		this.$body.empty();
	}

	show_skeleton() {
		hrms.hiring.clear(this.$body).append(skeleton_panel());
	}

	destroy() {
		this.loader.destroy();
		this.cancel_idle_render();
	}

	/** Shows an applicant; the one already shown is fetched again and redrawn only if it changed. */
	load(name) {
		if (name === this.name) return this.loader.refresh();
		this.cancel_idle_render();
		this.name = name;
		this.data = null;
		this.set_bar(null);
		return this.loader.show(name, {
			empty: () => this.show_row_header(name),
			skeleton: () => this.$body.append(skeleton_facts()),
			render: (data, { is_refresh, is_quiet }) => {
				if (!is_refresh) this.render(data, true);
				else if (is_quiet) this.render_when_idle(data);
				else this.render(data, false);
			},
			error: () =>
				hrms.hiring
					.clear(this.$body)
					.append(frappe.ui.empty_state({ title: __("Couldn't load this applicant") })),
		});
	}

	/** After a change made here (an email sent, a comment saved): draws it again even with focus still in the box. */
	reload(name) {
		this.loader.forget(name);
		if (name === this.name) return this.loader.refresh({ is_quiet: false });
	}

	forget(name) {
		this.loader.forget(name);
	}

	forget_all() {
		this.loader.forget_all();
	}

	/** What the row already knows shows at once: the name, the hold badge and the menu. */
	show_row_header(name) {
		const row = this.view.rows.find((row) => row.name === name);
		hrms.hiring.clear(this.$body);
		this.$scroll.scrollTop(0);
		if (!row) return;
		const { applicant_name, on_hold, group } = row;
		const stage = this.view.stage;
		this.$body.append(
			this.make_header({ name, applicant_name, on_hold, stage, interview_group: group }),
		);
	}

	/**
	 * Draws changed data for the shown applicant, but not under someone typing in it (a reply, a
	 * comment edit): then it waits until focus leaves the field and any press in the panel (Send, say) is done.
	 */
	render_when_idle(data) {
		const name = this.name;
		this.cancel_idle_render();
		const retry = () => setTimeout(() => this.name === name && this.render_when_idle(data));
		if (this.is_typing) return this.$el.one("focusout.idle", retry);
		if (this.$el[0].querySelector(":active"))
			return $(document).one("pointerup.hiring-idle", retry);
		this.render(data, false);
	}

	cancel_idle_render() {
		this.$el.off(".idle");
		$(document).off(".hiring-idle");
	}

	get is_typing() {
		const focused = document.activeElement;
		return (
			this.$el[0].contains(focused) &&
			(focused.isContentEditable || $(focused).is("input, textarea"))
		);
	}

	render(data, is_new) {
		const scroll_top = is_new ? 0 : this.$scroll.scrollTop();
		this.data = data;
		if (is_new || !this.mail_state)
			this.mail_state = hrms.hiring.ApplicantMail.create_state(data);
		this.$body
			.empty()
			.append(
				this.make_header(data),
				this.make_facts(data),
				this.make_interviews(data),
				this.make_offer_section(data),
				this.make_resume(data),
				this.make_cover_letter(data),
				this.make_mail(data),
			);
		this.set_bar(data);
		this.$scroll.scrollTop(scroll_top);
		this.limit_cover_letter();
	}

	make_mail(data) {
		return new hrms.hiring.ApplicantMail({
			data,
			state: this.mail_state,
			reload: () => this.reload(data.name),
		}).$el;
	}

	make_header(data) {
		const $name = $(`<h2 class="hiring__panel-name text-base-semibold"></h2>`).append(
			$("<span></span>").text(data.applicant_name),
		);
		if (data.on_hold) $name.append(frappe.ui.badge({ label: __("On hold"), size: "sm" }));
		const $meta = $(`<p class="hiring__panel-meta text-p-base"></p>`).append(
			this.make_stage(data),
		);
		return $(`<header class="hiring__panel-head"></header>`).append(
			$(`<div class="hiring__panel-identity"></div>`).append(
				frappe.ui.avatar({ label: data.applicant_name, size: "xl", theme: "auto" }),
				$(`<div class="hiring__panel-text"></div>`).append($name, $meta),
			),
			$(`<div class="hiring__panel-head-actions"></div>`).append(
				frappe.ui.button({
					label: __("Open profile"),
					icon_right: "arrow-up-right",
					variant: "ghost",
					onclick: () => frappe.set_route("Form", "Job Applicant", data.name),
				}),
				this.make_more_menu(data),
			),
		);
	}

	/** Secondary actions: an offer can be made from any stage before the interview round ends. */
	make_more_menu(data) {
		const options = this.get_more_options(data);
		if (!options.length) return null;
		return new frappe.ui.Dropdown({
			button: { icon: "ellipsis", variant: "ghost", tooltip: __("More actions") },
			align: "end",
			options,
		}).$trigger;
	}

	get_more_options(data) {
		if (data.stage === "Rejected") {
			return [
				{
					label: __("Move back"),
					icon: "rotate-ccw",
					onclick: () => this.move_back(data),
				},
			];
		}
		const can_offer = ["Applied", "Shortlisted", "Interviewing"].includes(data.stage);
		// the bar already carries a solid "Create offer" once the interviews are cleared
		const in_bar = this.get_actions(data).some((action) => action.id === "create_offer");
		if (!can_offer || in_bar) return [];
		return [
			{
				label: __("Create offer"),
				icon: "file-text",
				onclick: () => this.view.create_offer(data.name, data.applicant_name),
			},
		];
	}

	async move_back(data) {
		const { stage, stage_label } = await frappe.xcall(`${APPLICANT_API}.move_back_applicant`, {
			job_applicant: data.name,
		});
		this.forget(data.name);
		frappe.ui.toast({
			message: __("{0} moved back to {1}", [data.applicant_name, stage_label]),
		});
		// stay on this person: open the stage they landed in with them selected
		frappe.set_route(hrms.hiring.get_pipeline_route(this.view.name, stage, data.name));
	}

	make_meta_item(text) {
		return $(`<span class="hiring__panel-meta-item"></span>`).append(
			$("<span></span>").text(text),
		);
	}

	/** When they got to the stage, e.g. "Moved to Offered 3d ago"; "Applied 3d ago" for the first stage. */
	make_stage(data) {
		// the row has no stage line; a blank one keeps the header's height until it loads
		if (!data.stage_label) return "\u00a0";
		if (!data.stage_since) return this.make_meta_item(data.stage_label);
		const is_today = moment(data.stage_since).isSame(moment(), "day");
		const when = is_today ? __("today") : ago(data.stage_since);
		const text =
			data.stage === "Applied"
				? __("Applied {0}", [when])
				: __("Moved to {0} {1}", [data.stage_label, when]);
		return this.make_meta_item(text).attr(
			"title",
			frappe.datetime.str_to_user(data.stage_since),
		);
	}

	/** The sticky bar under the pane: step through applicants on the left, act on the right. */
	set_bar(data) {
		hrms.hiring
			.clear(this.$bar)
			.append(this.make_navigation(), this.make_actions(data))
			.show();
	}

	make_navigation() {
		const { index, total } = this.view.get_position();
		return $(`<div class="hiring__panel-nav"></div>`).append(
			frappe.ui.button({
				icon: "chevron-up",
				variant: "ghost",
				tooltip: __("Previous (K)"),
				disabled: index <= 1,
				onclick: () => this.view.step(-1),
			}),
			frappe.ui.button({
				icon: "chevron-down",
				variant: "ghost",
				tooltip: __("Next (J)"),
				disabled: index >= total,
				onclick: () => this.view.step(1),
			}),
			$(`<span class="hiring__panel-position text-p-sm"></span>`).text(
				__("{0} of {1}", [index, total]),
			),
		);
	}

	make_actions(data) {
		const $actions = $(`<div class="hiring__panel-actions"></div>`);
		for (const { id, ...button } of data ? this.get_actions(data) : []) {
			$actions.append(frappe.ui.button(button));
		}
		return $actions;
	}

	get_actions(data) {
		const item = { id: data.name, title: data.applicant_name };
		const shortlist = {
			id: "shortlist",
			label: __("Shortlist"),
			variant: "solid",
			onclick: () => this.view.shortlist(item),
		};
		const reject = {
			id: "reject",
			label: __("Reject"),
			theme: "red",
			onclick: () => this.view.reject(item),
		};
		const schedule = (variant) => ({
			id: "schedule",
			label: __("Schedule interview"),
			variant,
			onclick: () => this.schedule_interview(data),
		});
		const create_offer = {
			id: "create_offer",
			label: __("Create offer"),
			variant: "solid",
			onclick: () => this.view.create_offer(data.name, data.applicant_name),
		};
		const remind = {
			id: "remind",
			label: __("Remind interviewers"),
			variant: "solid",
			onclick: () => this.remind_interviewers(data),
		};
		// the main button follows the latest interview; while one is booked there is none
		const interviewing = {
			cleared: [reject, create_offer],
			not_cleared: [schedule("ghost"), { ...reject, variant: "solid" }],
			feedback_due: [reject, remind],
			scheduled: [reject],
			no_panel: [reject],
		};
		const actions = {
			Applied: () => [reject, shortlist],
			Shortlisted: () => [reject, schedule("solid")],
			Interviewing: () => interviewing[data.interview_group] || [reject, schedule("solid")],
			Offered: () => this.get_offer_actions(data),
			Hired: () => this.get_onboarding_actions(data),
			Rejected: () => [],
		};
		return actions[data.stage]();
	}

	/** A draft offer opens its form; a submitted one still waiting for the candidate is answered from here. */
	get_offer_actions(data) {
		const offer = data.offer;
		if (!offer) return [];
		const is_answerable =
			offer.docstatus === 1 && ["Ready to Send", "Awaiting Response"].includes(offer.status);
		if (!is_answerable) {
			return [
				{
					label: __("Open offer"),
					variant: "solid",
					onclick: () => frappe.set_route("Form", "Job Offer", offer.name),
				},
			];
		}
		return [
			{
				label: __("Mark declined"),
				onclick: () => this.decisions.set_offer_answer(offer, data, "Rejected"),
			},
			{
				label: __("Mark accepted"),
				variant: "solid",
				onclick: () => this.decisions.set_offer_answer(offer, data, "Accepted"),
			},
		];
	}

	get_onboarding_actions(data) {
		if (data.onboarding) {
			return [
				{
					label: __("View onboarding"),
					onclick: () =>
						frappe.set_route("Form", "Employee Onboarding", data.onboarding),
				},
			];
		}
		const offer = data.offer;
		if (!offer || offer.status !== "Accepted" || offer.docstatus !== 1) return [];
		return [
			{
				label: __("Start onboarding"),
				variant: "solid",
				onclick: () => frappe.new_doc("Employee Onboarding", { job_offer: offer.name }),
			},
		];
	}

	/** True when the bar already has a button that schedules an interview. */
	has_schedule_button(data) {
		return this.get_actions(data).some((action) => action.id === "schedule");
	}

	/** Opens the email composer on the current interview, to the panel members who haven't given feedback. */
	async remind_interviewers(data) {
		const interview = data.interviews.find((row) => row.name === data.current_interview);
		if (!interview) return;
		const doc = await frappe.db.get_doc("Interview", interview.name);
		const { interview_type, name, scheduled_on } = interview;
		const waiting = interview.panel.filter(
			(member) => !interview.feedback_from.includes(member.user),
		);
		const link = new URL(get_form_route("Interview", name), window.location.origin).href;
		const escape = frappe.utils.escape_html;
		new frappe.views.CommunicationComposer({
			doc,
			recipients: waiting.map((member) => member.user).join(", "),
			sender: data.email_sender || undefined,
			subject: __("Feedback reminder: {0} with {1}", [interview_type, data.applicant_name]),
			message: [
				__("Hi,"),
				"",
				escape(
					__("Could you submit your feedback for the {0} with {1} on {2}?", [
						interview_type,
						data.applicant_name,
						format_short_date(scheduled_on),
					]),
				),
				"",
				`<a href="${escape(link)}">${escape(name)}</a>`,
			].join("<br>"),
		});
	}

	async schedule_interview(data) {
		const { name, applicant_name, designation } = data;
		if (await hrms.hiring.schedule_interview({ name, applicant_name, designation }))
			this.view.after_scheduled(data);
	}

	/** Facts sit two per row, then one per row (the wide ones). */
	make_facts(data) {
		const $list = $(`<dl class="hiring__facts text-base"></dl>`);
		// each fact keeps its side; a missing one closes up, so a side never has a hole
		const rows = { left: 0, right: 0 };
		this.get_facts(data).forEach(([icon, label, value, title], index) => {
			if (!value) return;
			const is_wide = index >= 6;
			const column = index % 2 && !is_wide ? "right" : "left";
			// a wide fact starts below both sides
			if (is_wide) rows.left = Math.max(rows.left, rows.right);
			const slot = { "--row": ++rows[column] };
			const side = is_wide
				? "hiring__fact--wide"
				: column === "right"
				  ? "hiring__fact--right"
				  : "";
			const $value = $("<dd></dd>").addClass(side).css(slot).append(value);
			$list.append(
				$("<dt></dt>")
					.addClass(`${side} text-p-base`)
					.css(slot)
					.append(
						$(`<span class="hiring__fact-icon"></span>`).html(
							frappe.utils.icon(icon, "sm", "", "", "", true),
						),
						$("<span></span>").text(label),
					),
				$value.attr("title", title || $value.text()),
			);
		});
		return $list;
	}

	get_facts(data) {
		const link = (scheme, value) =>
			$("<a></a>").attr("href", `${scheme}:${value}`).text(value);
		return [
			[
				"calendar",
				__("Applied"),
				format_short_date(data.applied_on),
				frappe.datetime.str_to_user(data.applied_on, false, true),
			],
			[
				"git-branch",
				__("Source"),
				data.referred_by ? __("Referral · {0}", [data.referred_by]) : data.source,
			],
			["banknote", __("Expected salary"), this.format_salary_range(data)],
			[
				"star",
				__("Rating"),
				data.applicant_rating && __("{0} / 5", [Math.round(data.applicant_rating * 5)]),
			],
			["mail", __("Email"), data.email_id && link("mailto", data.email_id)],
			["phone", __("Phone"), data.phone_number && link("tel", data.phone_number)],
			// with a resume file, the link is usually a portfolio or profile (without one it is the resume)
			["link", __("Link"), data.resume_attachment && this.format_link(data.resume_link)],
			["circle-x", __("Reason"), data.stage === "Rejected" && this.format_rejection(data)],
		];
	}

	format_link(value) {
		const url = get_web_url(value);
		if (!url) return null;
		const label = `${url.host.replace(/^www\./, "")}${url.pathname.replace(/\/$/, "")}`;
		return $("<a></a>")
			.attr({ href: url.href, target: "_blank", rel: "noopener noreferrer" })
			.text(label);
	}

	/** The reason, with the team's note under it. */
	format_rejection({ rejection_reason, rejection_note }) {
		if (!rejection_reason) return null;
		const $value = $("<span></span>").text(rejection_reason);
		if (!rejection_note) return $value;
		return $value.add(
			$('<span class="hiring__fact-note text-p-sm"></span>').text(rejection_note),
		);
	}

	format_salary_range({ lower_range, upper_range, currency }) {
		const amounts = new Set([lower_range, upper_range].filter(Boolean));
		return [...amounts].map((amount) => format_currency(amount, currency, 0)).join(" – ");
	}

	make_interviews(data) {
		if (!data.interviews.length) return null;
		const items = data.interviews.map((interview) => ({
			id: interview.name,
			title: interview.interview_type,
			subtitle: this.get_interview_subtitle(interview),
			href: get_form_route("Interview", interview.name),
			controls: () => this.decisions.make_interview_controls(interview, data),
		}));
		return make_section(
			__("Interviews"),
			data.interviews.length,
			new frappe.ui.ItemList({ items }).$el,
			this.can_add_round(data) ? this.make_schedule_button(data) : null,
		);
	}

	// another round only while interviewing, and not when the bar's main button already schedules
	can_add_round(data) {
		return data.stage === "Interviewing" && !this.has_schedule_button(data);
	}

	make_schedule_button(data) {
		return frappe.ui.button({
			label: __("Schedule interview"),
			icon: "plus",
			variant: "ghost",
			size: "sm",
			onclick: () => this.schedule_interview(data),
		});
	}

	get_interview_subtitle(interview) {
		const feedback = interview.interviewer_count
			? __("{0} of {1} feedback in", [interview.feedback_count, interview.interviewer_count])
			: __("No interviewers yet");
		return [
			hrms.format_interview_time(interview.scheduled_on, interview.from_time),
			feedback,
			interview.average_rating != null && `★ ${interview.average_rating.toFixed(1)}`,
		]
			.filter(Boolean)
			.join(" · ");
	}

	/** The badge already says the state, so the subtitle only says when. */
	get_offer_subtitle(offer) {
		if (offer.status === "Cancelled") {
			return offer.offer_date && __("Made {0}", [format_short_date(offer.offer_date)]);
		}
		if (offer.docstatus === 0 || offer.status === "Ready to Send") {
			return __("Created {0}", [format_short_date(offer.creation)]);
		}
		return __("Sent {0}", [format_short_date(offer.offer_date || offer.creation)]);
	}

	make_offer_section(data) {
		const offer = data.offer;
		if (!offer) return null;
		const subtitle = this.get_offer_subtitle(offer);
		const item = {
			id: offer.name,
			title: __("Job offer"),
			subtitle,
			href: get_form_route("Job Offer", offer.name),
		};
		return make_section(
			__("Offer"),
			null,
			new frappe.ui.ItemList({
				items: [
					{ ...item, controls: () => this.decisions.make_offer_controls(offer, data) },
				],
			}).$el,
		);
	}

	make_resume(data) {
		const attachment = get_web_url(data.resume_attachment);
		const link = get_web_url(data.resume_link);
		const url = attachment || link;
		if (!url) {
			const note = data.resume_missing
				? __("Resume file not found")
				: __("No resume attached");
			return make_section(
				__("Resume"),
				null,
				$(`<p class="hiring__resume-note text-p-base"></p>`).text(note),
			);
		}
		const file = attachment ? this.get_file_row(data, url) : this.get_link_row(url);
		const $box = $(`<div class="hiring__resume"></div>`);
		const is_pdf = attachment?.pathname.toLowerCase().endsWith(".pdf");
		const $preview = is_pdf ? this.make_preview(file.title, url) : null;
		$box.append(this.make_file_row(file, url), $preview);
		if ($preview) queueMicrotask(() => this.render_preview($box, $preview, file, url));
		return make_section(__("Resume"), null, $box);
	}

	make_preview(title, url) {
		const $paper = $(`<div class="hiring__resume-paper"></div>`).append(
			frappe.ui.skeleton.html({ height: "296px", width: "100%" }),
		);
		// scrolls inside its own box; the file row's Open still opens the PDF
		return $(`<div class="hiring__resume-preview" tabindex="0"></div>`)
			.attr("aria-label", title)
			.append($paper);
	}

	/** Draws page 1 with pdf.js, loaded only when a resume shows; on failure only the file row stays. */
	async render_preview($box, $preview, file, url) {
		const $paper = $preview.find(".hiring__resume-paper");
		try {
			await frappe.require("resume_preview.bundle.js");
			const { page_count } = await hrms.render_resume_preview($paper[0], url.href);
			if (page_count > 1) {
				const pages = __("{0} pages", [page_count]);
				$box.find(".hiring__file-subtitle").text(
					[file.subtitle, pages].filter(Boolean).join(" · "),
				);
			}
		} catch (error) {
			console.warn("Resume preview failed", error);
			$preview.remove();
		}
	}

	get_file_row(data, url) {
		const uploaded =
			data.resume_uploaded_on &&
			__("Uploaded {0}", [format_short_date(data.resume_uploaded_on)]);
		return {
			icon: "file-text",
			title: data.resume_file_name || decodeURIComponent(url.pathname.split("/").pop()),
			subtitle: uploaded,
		};
	}

	get_link_row(url) {
		return { icon: "link", title: __("Resume link"), subtitle: url.host };
	}

	make_file_row({ icon, title, subtitle }, url) {
		return $(`<div class="hiring__file"></div>`).append(
			$(`<span class="hiring__file-icon"></span>`).html(
				frappe.utils.icon(icon, "sm", "", "", "", true),
			),
			$(`<span class="hiring__file-text"></span>`).append(
				$(`<span class="hiring__file-title text-p-base-medium"></span>`).text(title),
				subtitle &&
					$(`<span class="hiring__file-subtitle text-p-sm"></span>`).text(subtitle),
			),
			frappe.ui.button({
				label: __("Open"),
				icon_right: "arrow-up-right",
				variant: "ghost",
				onclick: () => open_in_new_tab(url),
			}),
		);
	}

	make_cover_letter(data) {
		if (!data.cover_letter) return null;
		const $text = $(`<p class="hiring__cover-letter text-p-base"></p>`).text(
			data.cover_letter,
		);
		const $toggle = frappe.ui
			.button({
				label: __("Show more"),
				variant: "ghost",
				onclick: () => {
					const is_open = $text[0].toggleAttribute("data-expanded");
					$toggle
						.find(".es-button__label")
						.text(is_open ? __("Show less") : __("Show more"));
				},
			})
			.addClass("hiring__cover-letter-toggle")
			.hide();
		return make_section(__("Cover letter"), null, [$text, $toggle]);
	}

	limit_cover_letter() {
		const text = this.$body.find(".hiring__cover-letter")[0];
		if (text && text.scrollHeight > text.clientHeight + 1) {
			this.$body.find(".hiring__cover-letter-toggle").show();
		}
	}
};
