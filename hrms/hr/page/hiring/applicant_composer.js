/**
 * One bordered box for writing: the text grows with what's typed, and the bar inside it holds
 * `start` content on the left and the shortcut hint, `end` buttons and the submit button on the right.
 */
hrms.hiring.make_composer = ({
	placeholder,
	label,
	rows = 2,
	value = "",
	drafts,
	draft_key,
	submit,
	on_submit,
	start = [],
	end = [],
	on_escape,
	letter,
}) => {
	const $input = $(`<textarea class="hiring__composer-input text-p-base"></textarea>`)
		.attr({ rows, placeholder, "aria-label": label })
		.val(drafts ? drafts.get(draft_key) || "" : value);
	const $submit = frappe.ui.button({
		label: submit.label,
		icon: submit.icon,
		variant: submit.variant || "subtle",
		size: "sm",
		tooltip: submit.tooltip,
		onclick: () => on_submit($input.val()),
	});
	const grow = () => {
		const el = $input[0];
		el.style.height = "auto";
		el.style.height = `${el.scrollHeight}px`;
	};
	const sync = () => {
		if (drafts) drafts.set(draft_key, $input.val());
		$submit.prop("disabled", !$input.val().trim());
		grow();
	};
	let box = null;
	$input.on("input", sync).on("keydown", (event) => {
		if (event.key === "Escape" && (box || on_escape)) {
			event.preventDefault();
			event.stopPropagation();
			box ? box.close() : on_escape();
		} else if (is_submit_key(event)) {
			event.preventDefault();
			event.stopPropagation();
			if (!$submit.prop("disabled")) $submit.trigger("click");
		}
	});
	const $el = letter
		? null
		: $(`<div class="hiring__composer"></div>`).append(
				$input,
				make_composer_bar({ start, end, $submit }),
		  );
	sync();
	if (letter) box = make_letter_shell({ $input, $submit, letter, placeholder, grow });
	// a draft restored into a box that isn't in the page yet has no height to measure
	requestAnimationFrame(grow);
	const set_value = (text) => {
		$input.val(text);
		sync();
		$input.trigger("focus");
	};
	return { $el: box ? box.$el : $el, $input, get_value: () => $input.val(), set_value };
};

function make_composer_bar({ start, end, $submit }) {
	const hint = is_mac_platform() ? "⌘↵" : "Ctrl+↵";
	return $(`<div class="hiring__composer-bar"></div>`).append(
		$(`<div class="hiring__composer-start"></div>`).append(start),
		$(`<span class="hiring__composer-hint text-p-sm"></span>`).text(hint),
		end,
		$submit,
	);
}

/** Wraps the textarea in the letter: a one-line peek at rest, the To row, subject and footer when open. */
function make_letter_shell({ $input, $submit, letter, placeholder, grow }) {
	const $peek = $(`<button type="button" class="hiring__letter-peek text-p-base"></button>`);
	const $peek_text = $(`<span class="hiring__letter-peek-text"></span>`);
	const $draft = frappe.ui
		.badge({ label: __("Draft"), theme: "gray", size: "sm" })
		.addClass("hiring__letter-draft");
	$peek.append($peek_text, $draft);
	const $el = $(`<div class="hiring__composer hiring__letter" data-open="false"></div>`);
	let is_returning = false;
	const refresh_peek = () => {
		const draft = $input.val().replace(/\s+/g, " ").trim();
		$peek_text.text(draft || placeholder).attr("data-placeholder", draft ? null : "");
		$draft.toggle(Boolean(draft));
	};
	const open = () => {
		if ($el.attr("data-open") === "true") return;
		$el.attr("data-open", "true");
		grow();
		$input.trigger("focus");
	};
	const close = () => {
		$el.attr("data-open", "false");
		refresh_peek();
		is_returning = true;
		$peek.trigger("focus");
		is_returning = false;
	};
	$peek.on("click", open).on("focus", () => !is_returning && open());
	const $close = frappe.ui.button({
		icon: "x",
		variant: "ghost",
		size: "sm",
		tooltip: { text: __("Close, keep draft"), shortcut: ["Esc"], side: "bottom" },
		onclick: close,
	});
	$el.on("keydown", (event) => {
		if (event.key !== "Escape" || event.isDefaultPrevented()) return;
		event.stopPropagation();
		close();
	});
	const $bar = $(`<div class="hiring__composer-bar"></div>`).append(
		$(`<div class="hiring__composer-start"></div>`).append(letter.tools),
		letter.from,
		$submit,
	);
	$input.on("input", refresh_peek);
	refresh_peek();
	$el.append(
		$peek,
		make_letter_to(letter, $close),
		$(`<div class="hiring__letter-subject"></div>`).append(letter.$subject),
		$input,
		$bar,
	);
	return { $el, close };
}

function make_letter_to({ to_name, to_address }, $close) {
	const $address = $(`<span class="hiring__letter-address"></span>`).text(to_address);
	frappe.ui.tooltip($address, { only_on_overflow: true, side: "bottom" });
	return $(`<div class="hiring__letter-to text-p-base"></div>`).append(
		$(`<span class="hiring__letter-label"></span>`).text(__("To")),
		$(`<span class="hiring__letter-name text-p-base-medium"></span>`).text(to_name),
		$address,
		$close,
	);
}

function is_submit_key(event) {
	return event.key === "Enter" && (event.metaKey || event.ctrlKey);
}

function is_mac_platform() {
	return /Mac|iPhone|iPad/.test(navigator.platform);
}
