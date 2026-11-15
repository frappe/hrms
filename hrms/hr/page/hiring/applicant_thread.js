// longer threads keep the first email and the last two, the rest stacked in between
const LONG_THREAD = 10;
const UNSENT_STATES = ["Sending", "Scheduled"];
const FAILED_STATES = ["Error", "Bounced", "Rejected"];
const GREETING = /^(hi|hello|hey|dear)\b[^\n]{0,40}$/i;

const EASE_OUT = "cubic-bezier(0.23, 1, 0.32, 1)";

/**
 * A re-rendered mail card grows or shrinks from its old height while the old face fades out on
 * top of the new one (a crossfade), so folding never swaps the layout in one frame.
 * Reduced motion keeps only a short fade.
 */
function animate_card_height(card, old_card, from, is_opening) {
	if (!card || !old_card || !from || !card.animate) return;
	if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
		card.animate([{ opacity: 0.6 }, { opacity: 1 }], { duration: 150, easing: "ease" });
		return;
	}
	const to = card.offsetHeight;
	if (from === to) return;
	const duration = is_opening ? 200 : 180;
	const ghost = make_ghost(old_card, from);
	card.style.position = "relative";
	card.append(ghost);
	card.animate(
		[
			{ height: `${from}px`, overflow: "hidden" },
			{ height: `${to}px`, overflow: "hidden" },
		],
		{ duration, easing: EASE_OUT },
	);
	// the old face leaves fast, the new one arrives just behind it; a 2px blur hides the overlap
	ghost
		.animate(
			[
				{ opacity: 1, filter: "blur(0)" },
				{ opacity: 0, filter: "blur(2px)" },
			],
			{ duration: duration * 0.6, easing: EASE_OUT, fill: "forwards" },
		)
		.finished.finally(() => {
			ghost.remove();
			card.style.removeProperty("position");
		});
	for (const part of card.children) {
		if (part === ghost) continue;
		part.animate([{ opacity: 0 }, { opacity: 1 }], {
			duration,
			delay: duration * 0.25,
			easing: EASE_OUT,
			fill: "backwards",
		});
	}
}

/** A frozen copy of the card's old face, laid over the new card while it fades out. */
function make_ghost(old_card, height) {
	const ghost = old_card.cloneNode(true);
	ghost.removeAttribute("data-email");
	ghost.setAttribute("aria-hidden", "true");
	ghost.inert = true;
	Object.assign(ghost.style, {
		position: "absolute",
		inset: "0 0 auto 0",
		height: `${height}px`,
		margin: "0",
		border: "0",
		background: "transparent",
		pointerEvents: "none",
	});
	return ghost;
}

function slide_from(card, offset) {
	card.animate([{ transform: `translateY(${offset}px)` }, { transform: "none" }], {
		duration: 230,
		easing: EASE_OUT,
	});
}

/** The subject an email shows: only when it starts a new conversation. */
function get_new_subject(email, previous) {
	const subject = email.subject;
	if (
		!subject ||
		(previous && strip_reply_prefix(previous.subject) === strip_reply_prefix(subject))
	)
		return null;
	return subject;
}

/** The first words of a mail: its own text, without quoted replies or a "Hi Name," line. */
function get_snippet(html) {
	const text = hrms.hiring.html_to_text(
		(html || "").replace(/<blockquote[\s\S]*<\/blockquote>/i, ""),
	);
	const lines = text.split("\n").filter((line) => line.trim());
	if (lines.length > 1 && GREETING.test(lines[0].trim())) lines.shift();
	return lines.join(" ").replace(/\s+/g, " ");
}

function strip_reply_prefix(subject) {
	return (subject || "").replace(/^\s*re\s*:\s*/i, "").trim();
}

function format_mail_time(datetime, short) {
	const date = moment(datetime);
	const time = date.format("h:mm a");
	if (date.isSame(moment(), "day")) return short ? time : __("Today, {0}", [time]);
	const is_yesterday = date.isSame(moment().subtract(1, "day"), "day");
	if (short) return is_yesterday ? __("Yesterday") : date.format("D MMM");
	return `${is_yesterday ? __("Yesterday") : date.format("D MMM")}, ${time}`;
}

/** "Name <a@b.com>, c@d.com" into [{ name, address }]. */
function parse_addresses(value) {
	return (value || "")
		.split(",")
		.map((part) => part.trim())
		.filter(Boolean)
		.map((part) => {
			const match = part.match(/^(.*)<(.+)>$/);
			return match
				? { name: match[1].trim().replace(/^"|"$/g, ""), address: match[2].trim() }
				: { name: "", address: part };
		});
}

/** The applicant's email thread: cards that fold and open, the pile of a long thread, each mail's envelope. */
hrms.hiring.ApplicantThread = class ApplicantThread {
	/** `on_reply(email)` opens the full composer on a mail, offered when `can_reply`. */
	constructor({ data, state, can_reply, on_reply }) {
		this.data = data;
		this.state = state;
		this.can_reply = can_reply;
		this.on_reply = on_reply;
		this.$thread = $(`<div class="hiring__mail-thread"></div>`);
		this.render_thread();
	}

	/** Open cards: the latest mail and any that were unread, unless folded by hand. */
	is_open(email, latest) {
		if (email === latest) return true;
		if (this.state.open.has(email.name)) return this.state.open.get(email.name);
		return this.state.unread.has(email.name);
	}

	set_open(email, is_open) {
		const old_card = this.find_card(email);
		const from = old_card?.offsetHeight;
		this.state.open.set(email.name, is_open);
		this.render_thread();
		animate_card_height(this.find_card(email), old_card, from, is_open);
	}

	find_card(email) {
		return this.$thread?.[0].querySelector(`[data-email="${CSS.escape(email.name)}"]`);
	}

	render_thread() {
		const { emails } = this.data;
		const latest = emails[emails.length - 1];
		const is_long = emails.length > LONG_THREAD && !this.state.show_earlier;
		const nodes = [];
		emails.forEach((email, index) => {
			if (is_long && index >= 1 && index < emails.length - 2) return;
			const $card = this.make_card(email, { latest, previous: emails[index - 1] });
			// the hidden middle is piled under the first email
			nodes.push(is_long && index === 0 ? this.make_pile($card, emails.length - 3) : $card);
		});
		hrms.hiring.clear(this.$thread).append(nodes);
	}

	/** The first email with the hidden middle piled under it; its edges open the pile. */
	make_pile($first, count) {
		// the peeking edges are the button; the count lives in its tooltip and accessible name
		const label = __("Show {0} more emails", [count]);
		const $edges = $(`<button type="button" class="hiring__mail-pile-edges"></button>`)
			.attr({ "aria-expanded": "false", "aria-label": label })
			.on("click", () => this.unstack());
		frappe.ui.tooltip($edges, { text: label, side: "bottom", delay: 200 });
		return $(`<div class="hiring__mail-pile"></div>`).append($first, $edges);
	}

	/** Opens the stack: the shown cards slide to their new places and the hidden ones fan out of the pile. */
	unstack() {
		const thread = this.$thread[0];
		const stack = thread.querySelector(".hiring__mail-pile > [data-email]");
		const before = new Map(
			[...thread.querySelectorAll("[data-email]")].map((card) => [
				card.dataset.email,
				card.getBoundingClientRect().top,
			]),
		);
		const stack_top = stack?.getBoundingClientRect().top;
		this.state.show_earlier = true;
		this.render_thread();
		if (stack_top === undefined || !thread.animate) return;
		const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
		// the first email stays on top while the others slide out from under it
		const first = thread.querySelector("[data-email]");
		first.style.position = "relative";
		first.style.zIndex = "101";
		const slides = [];
		let revealed = 0;
		for (const card of thread.querySelectorAll("[data-email]")) {
			const top = card.getBoundingClientRect().top;
			const was = before.get(card.dataset.email);
			if (was !== undefined) {
				if (!reduce && was !== top) slide_from(card, was - top);
				continue;
			}
			if (reduce) {
				card.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 150, easing: "ease" });
				continue;
			}
			// each card slides out from under the one above it, so the pile never shows through itself
			card.style.position = "relative";
			card.style.zIndex = String(100 - revealed);
			const delay = Math.min(revealed++ * 15, 90);
			const slide = card.animate(
				[
					{ transform: `translateY(${stack_top - top}px) scale(0.98)` },
					{ transform: "none" },
				],
				{ duration: 230, delay, easing: EASE_OUT, fill: "backwards" },
			);
			card.animate([{ opacity: 0 }, { opacity: 1 }], {
				duration: 120,
				delay,
				easing: "ease",
				fill: "backwards",
			});
			slides.push(slide.finished.then(() => card.style.removeProperty("z-index")));
		}
		Promise.allSettled(slides).then(() => first.style.removeProperty("z-index"));
	}

	make_card(email, context) {
		const is_open = this.is_open(email, context.latest);
		const $card = is_open
			? this.make_open_card(email, context)
			: this.make_folded_card(email, context);
		return $card.attr("data-email", email.name);
	}

	get_sender_name(email) {
		if (email.sender === frappe.session.user_email) return __("You");
		return email.sender_full_name || parse_addresses(email.sender)[0]?.address || email.sender;
	}

	/** The time at the right of a card, or its delivery state when the mail isn't sitting in an inbox yet. */
	make_time(email, short) {
		if (UNSENT_STATES.includes(email.delivery_status)) {
			return $(`<span class="hiring__mail-time text-p-sm"></span>`).text(__("Sending"));
		}
		if (FAILED_STATES.includes(email.delivery_status)) {
			return $(`<span class="hiring__mail-time text-p-sm" data-failed></span>`).text(
				__("Not delivered"),
			);
		}
		return $(`<span class="hiring__mail-time text-p-sm"></span>`)
			.text(format_mail_time(email.communication_date, short))
			.attr("title", frappe.datetime.str_to_user(email.communication_date));
	}

	make_new_marker(email) {
		if (!this.state.unread.has(email.name)) return null;
		return $(`<span class="hiring__mail-new text-p-sm-medium"></span>`).append(
			$(`<span class="hiring__mail-dot"></span>`),
			$("<span></span>").text(__("New")),
		);
	}

	make_folded_card(email, { previous }) {
		const name = this.get_sender_name(email);
		const subject = get_new_subject(email, previous);
		const $snippet = $(`<span class="hiring__mail-fold-snippet"></span>`).text(
			get_snippet(email.content),
		);
		if (subject)
			$snippet.prepend(
				$(`<span class="hiring__mail-fold-subject"></span>`).text(subject),
				" · ",
			);
		return $(
			`<button type="button" class="hiring__mail-card hiring__mail-fold text-p-base"></button>`,
		)
			.attr("aria-expanded", "false")
			.append(
				frappe.ui.avatar({ label: name, size: "md", theme: "auto" }),
				$(`<span class="hiring__mail-fold-name text-p-base-medium"></span>`).text(name),
				this.make_new_marker(email),
				$snippet,
				this.make_time(email, true),
			)
			.on("click", () => this.set_open(email, true));
	}

	make_open_card(email, { latest, previous }) {
		const is_latest = email === latest;
		const $card = $(`<article class="hiring__mail-card hiring__mail-open"></article>`);
		const $head = $(`<header class="hiring__mail-card-head"></header>`).append(
			this.make_sender(email),
			$(`<div class="hiring__mail-card-side"></div>`).append(
				this.make_time(email, false),
				this.make_menu(email),
			),
		);
		if (!is_latest) {
			$head.attr("data-foldable", "").on("click", (event) => {
				if (!$(event.target).closest("button, a, .es-menu").length)
					this.set_open(email, false);
			});
		}
		$card.append($head);
		const $envelope = this.state.envelopes.has(email.name) ? this.make_envelope(email) : null;
		$card.append($envelope);
		$card.append(this.make_body(email, previous));
		return $card;
	}

	make_sender(email) {
		const name = this.get_sender_name(email);
		const [first] = parse_addresses(email.recipients);
		const recipient = this.get_recipient_name(first);
		const is_envelope_open = this.state.envelopes.has(email.name);
		const $toggle = $(`<button type="button" class="hiring__mail-to text-p-sm"></button>`)
			.attr("aria-expanded", String(is_envelope_open))
			.append(
				$("<span></span>").text(__("to {0}", [recipient])),
				$(`<span class="hiring__mail-icon"></span>`)
					.toggleClass("hiring__mail-icon--open", is_envelope_open)
					.html(frappe.utils.icon("chevron-down", "xs", "", "", "", true)),
			)
			.on("click", () => this.toggle_envelope(email));
		const has_name = name !== email.sender;
		const $line = $(`<div class="hiring__mail-sender-line text-p-base"></div>`).append(
			$(`<span class="hiring__mail-sender-name text-p-base-medium"></span>`).text(name),
			has_name &&
				$(`<span class="hiring__mail-sender-address text-p-sm"></span>`).text(
					`<${email.sender}>`,
				),
			this.make_new_marker(email),
		);
		return $(`<div class="hiring__mail-sender"></div>`).append(
			frappe.ui.avatar({ label: name, size: "md", theme: "auto" }),
			$(`<div class="hiring__mail-sender-text"></div>`).append($line, $toggle),
		);
	}

	get_recipient_name(recipient) {
		if (!recipient) return __("unknown");
		if (recipient.address === this.data.email_id) return this.data.applicant_name;
		if (recipient.address === frappe.session.user_email) return __("me");
		return recipient.name || recipient.address;
	}

	/** The From/To/Date block opens like a dropdown: the same 180ms ease-out, scale 0.97, 2px. */
	toggle_envelope(email) {
		const { envelopes } = this.state;
		const from = this.find_card(email)?.offsetHeight;
		const is_opening = !envelopes.has(email.name);
		is_opening ? envelopes.add(email.name) : envelopes.delete(email.name);
		this.render_thread();
		const card = this.find_card(email);
		if (!card?.animate || window.matchMedia("(prefers-reduced-motion: reduce)").matches)
			return;
		const to = card.offsetHeight;
		card.animate(
			[
				{ height: `${from}px`, overflow: "hidden" },
				{ height: `${to}px`, overflow: "hidden" },
			],
			{
				duration: is_opening ? 180 : 140,
				easing: EASE_OUT,
			},
		);
		card.querySelector(".hiring__mail-icon")?.animate(
			[
				{ transform: `rotate(${is_opening ? 0 : 180}deg)` },
				{ transform: `rotate(${is_opening ? 180 : 0}deg)` },
			],
			{ duration: 180, easing: EASE_OUT },
		);
		if (is_opening) {
			card.querySelector(".hiring__mail-envelope")?.animate(
				[
					{ opacity: 0, transform: "scale(0.97) translateY(-2px)" },
					{ opacity: 1, transform: "none" },
				],
				{ duration: 180, easing: EASE_OUT },
			);
		}
	}

	make_envelope(email) {
		const rows = [
			[
				__("From"),
				email.sender_full_name
					? `${email.sender_full_name} <${email.sender}>`
					: email.sender,
			],
			[__("To"), email.recipients],
			[__("Cc"), email.cc],
			[__("Date"), moment(email.communication_date).format("ddd D MMM YYYY, h:mm a")],
			[__("Subject"), email.subject],
		];
		const $list = $(`<dl class="hiring__mail-envelope text-p-sm"></dl>`);
		for (const [label, value] of rows) {
			if (!value) continue;
			$list.append(
				$('<dt class="text-p-sm"></dt>').text(label),
				$("<dd></dd>").text(value).attr("title", value),
			);
		}
		return $list;
	}

	make_menu(email) {
		const options = [
			{
				label: __("Reply in full editor"),
				icon: "reply",
				onclick: () => this.on_reply(email),
			},
			{ label: __("Copy text"), icon: "copy", onclick: () => this.copy_text(email) },
		];
		if (!this.can_reply) options.shift();
		return frappe.ui.dropdown({
			button: { icon: "ellipsis", variant: "ghost", tooltip: __("More") },
			align: "end",
			options,
		});
	}

	copy_text(email) {
		const text = hrms.hiring.html_to_text(email.content);
		const copied = () => frappe.ui.toast({ message: __("Copied") });
		navigator.clipboard.writeText(text).then(copied, () => {
			// no clipboard permission: fall back to the legacy copy
			const $field = $("<textarea></textarea>").val(text).appendTo("body").select();
			document.execCommand("copy");
			$field.remove();
			copied();
		});
	}

	make_body(email, previous) {
		const $body = $(`<div class="hiring__mail-body text-p-base"></div>`);
		const subject = get_new_subject(email, previous);
		if (subject) {
			$body.append(
				$(`<p class="hiring__mail-subject text-p-base-semibold"></p>`).text(subject),
			);
		}
		const $content = $(`<div class="hiring__mail-text"></div>`).html(
			frappe.dom.remove_script_and_style(email.content),
		);
		this.collapse_quotes($content);
		return $body.append($content);
	}

	/** Quoted earlier mails hide behind a "•••" toggle, as in the form timeline. */
	collapse_quotes($content) {
		$content
			.find("blockquote")
			.filter((_, quote) => !$(quote).parent().closest("blockquote").length)
			.each((_, quote) => {
				const $quote = $(quote).hide();
				const $toggle = $(
					`<button type="button" class="hiring__mail-quote-toggle"></button>`,
				)
					.text("•••")
					.attr({ "aria-expanded": "false", "aria-label": __("Show quoted text") })
					.on("click", () => {
						const is_open = $quote.toggle().is(":visible");
						$toggle.attr("aria-expanded", String(is_open));
					});
				$quote.before($toggle);
			});
	}
};
