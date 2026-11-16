frappe.provide("hrms.hiring");

/** Empties an element, destroying its tooltips so none stay stuck on screen. */
hrms.hiring.clear = ($element) => {
	$element.find("*").each((_, node) => $(node).data("es-tooltip")?.destroy());
	return $element.empty();
};

const API = "hrms.hr.page.hiring.hiring";
const REALTIME_DOCTYPES = ["Job Applicant", "Interview", "Job Offer"];
const APPLICANT_API = "hrms.hr.page.hiring.applicant";
const SPLIT_QUERY = "(min-width: 1024px)";
const PAGE_LENGTH = 50;
const STAGES = ["Applied", "Shortlisted", "Interviewing", "Offered", "Hired", "Rejected"];

function get_empty_descriptions() {
	return {
		Applied: __("New applications land here first."),
		Shortlisted: __("Applicants you shortlist wait here until their first interview is booked."),
		Interviewing: __("Applicants move here once their first interview is booked."),
		Offered: __("Offers you make show here until the applicant replies."),
		Hired: __("Applicants who accept an offer show here."),
		Rejected: __("Rejected applicants show here."),
	};
}

const SORTS = ["newest", "oldest", "rating"];

function get_sort_labels() {
	return { newest: __("Newest"), oldest: __("Oldest"), rating: __("Rating") };
}

function ago(datetime) {
	const short = frappe.datetime.prettyDate(datetime, true);
	if (!short) return "";
	return short === __("now") ? short : __("{0} ago", [short.replace(/\s/g, "")]);
}

function get_form_route(doctype, name) {
	return `/desk/${frappe.router.slug(doctype)}/${encodeURIComponent(name)}`;
}

function get_route_key(opening, stage, applicant) {
	return JSON.stringify([opening, stage, applicant || ""]);
}

function skeleton_bar(width, height) {
	return frappe.ui.skeleton.html({ width, height, css_class: "hiring__skeleton-bar" });
}

function skeleton_row({ has_avatar = false, has_meta = false } = {}) {
	const avatar = has_avatar
		? `<span class="es-item-list__lead">${frappe.ui.skeleton.html({
				css_class: "hiring__skeleton-avatar",
		  })}</span>`
		: "";
	const meta = has_meta ? `<span class="es-item-list__meta">${skeleton_bar("72px", "10px")}</span>` : "";
	return `<div class="es-item-list__row" ${has_avatar ? "data-avatar" : ""}>
		${avatar}
		<span class="es-item-list__text">
			<span class="es-item-list__title">${skeleton_bar(has_avatar ? "50%" : "40%", "12px")}</span>
			<span class="es-item-list__subtitle">${skeleton_bar(has_avatar ? "35%" : "25%", "10px")}</span>
		</span>
		${meta}
	</div>`;
}

/** Placeholder rows in the shape of an ItemList: boxed on the overview, flat in the split pane. */
function skeleton_list(count, { variant = "boxed", ...row_options } = {}) {
	const rows = Array.from({ length: count }, () => skeleton_row(row_options)).join("");
	const flat = variant === "flat" ? `data-variant="flat"` : "";
	return $(`<div class="es-item-list" ${flat} aria-hidden="true">${rows}</div>`);
}

function skeleton_overview() {
	const heading = `<h2 class="hiring__heading text-base-semibold"><span>${skeleton_bar("96px", "14px")}</span></h2>`;
	return $(`<section class="hiring__section"></section>`).append(
		heading,
		skeleton_list(3, { has_meta: true }),
	);
}

function skeleton_facts() {
	const facts = Array.from({ length: 6 }, (_, index) => {
		const attrs = `class="${index % 2 ? "hiring__fact--right" : ""}" style="--row: ${Math.floor(index / 2) + 1}"`;
		return `<dt ${attrs}>${skeleton_bar("88px", "12px")}</dt><dd ${attrs}>${skeleton_bar("60%", "12px")}</dd>`;
	}).join("");
	return `<dl class="hiring__facts text-base">${facts}</dl>`;
}

function skeleton_panel() {
	return $(`<div class="hiring__skeleton" aria-hidden="true">
		<div class="hiring__panel-head">
			<div class="hiring__panel-identity">
				${frappe.ui.skeleton.html({ css_class: "hiring__skeleton-avatar", width: "32px", height: "32px" })}
				<div class="hiring__panel-text hiring__skeleton-text">
					${skeleton_bar("30%", "14px")}${skeleton_bar("45%", "12px")}
				</div>
			</div>
		</div>
		${skeleton_facts()}
	</div>`);
}

function make_heading(label, count, actions) {
	const $heading = $(`<h2 class="hiring__heading text-base-semibold"></h2>`);
	$heading.append($("<span></span>").text(label));
	if (count) $heading.append(frappe.ui.badge({ label: String(count), size: "sm" }));
	if (actions) $heading.append($(`<span class="hiring__heading-actions"></span>`).append(actions));
	return $heading;
}

frappe.pages["hiring"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Hiring pipeline"),
		single_column: true,
	});
	wrapper.hiring = new hrms.hiring.Hiring(page);
	$(wrapper).on("show", () => {
		wrapper.hiring.listen();
		// selecting an applicant rewrites the URL; the desk must not scroll to top for it
		wrapper.disable_scroll_to_top = wrapper.hiring.show();
	});
	$(wrapper).on("hide", () => wrapper.hiring.unlisten());
};

hrms.hiring.Hiring = class Hiring {
	constructor(page) {
		this.page = page;
		this.$body = $(`<div class="hiring"></div>`).appendTo(page.main);
		this.opening_view = null;
		this.request_id = 0;
		this.is_listening = false;
		this.overview_filter = { search: "", department: null, location: null, sort: "attention" };
		this.bind_shortcuts();
	}

	/**
	 * Applicants, interviews and offers change in other tabs and in the forms; while the page is
	 * showing, such a change refreshes it (debounced), keeping the selection. Only this page's own
	 * handler is removed on hide, so list views keep theirs.
	 */
	listen() {
		// "show" fires on every route change inside the page; subscribe once per show and hide
		if (this.is_listening) return;
		this.is_listening = true;
		this.refresh_soon ||= frappe.utils.debounce((data) => this.refresh_from_update(data), 800);
		// every change drops its applicant from the panel's memory; the debounced refresh sees only the last
		this.handle_update ||= (data) => {
			this.opening_view?.forget_changed(data);
			this.refresh_soon(data);
		};
		frappe.realtime.on("list_update", this.handle_update);
		for (const doctype of REALTIME_DOCTYPES) frappe.realtime.doctype_subscribe(doctype);
	}

	unlisten() {
		if (!this.is_listening) return;
		this.is_listening = false;
		frappe.realtime.off("list_update", this.handle_update);
		for (const doctype of REALTIME_DOCTYPES) frappe.realtime.doctype_unsubscribe(doctype);
	}

	refresh_from_update(data) {
		if (!REALTIME_DOCTYPES.includes(data?.doctype)) return;
		if (frappe.get_route()[0] !== "hiring") return;
		this.opening_view?.refresh_from_update();
	}

	/** Left and right step through the stages; the split binds j, k, up and down for applicants (see OpeningView.mount_pane). */
	bind_shortcuts() {
		for (const [shortcut, delta, description] of [
			["right", 1, __("Next stage")],
			["left", -1, __("Previous stage")],
		]) {
			frappe.ui.keys.add_shortcut({
				shortcut,
				description,
				page: this.page,
				// an empty stage has no split, and stepping past it still has to work
				condition: () => this.can_step(shortcut, { needs_split: false }),
				action: () => this.opening_view.step_stage(delta),
			});
		}
	}

	can_step(shortcut, { needs_split = true } = {}) {
		const focused = document.activeElement;
		const is_arrow = ["up", "down", "left", "right"].includes(shortcut);
		const owns_arrows = is_arrow && focused?.closest("[role=radiogroup], [role=menu], .es-menu, [aria-haspopup]");
		const is_blocked = focused?.isContentEditable || owns_arrows || $(".modal:visible").length;
		const view = this.opening_view;
		const has_layout = needs_split ? view?.is_split : view?.media.matches;
		return Boolean(has_layout) && !is_blocked;
	}

	is_active(view) {
		return this.opening_view === view && frappe.get_route()[0] === "hiring";
	}

	/** Returns true when the route only echoes a selection made on the page. */
	show() {
		const [, opening, stage, applicant] = frappe.get_route();
		if (opening) return this.show_opening(opening, stage, applicant);
		this.leave_opening();
		this.show_overview();
		return false;
	}

	leave_opening() {
		this.opening_view?.destroy();
		this.opening_view = null;
		this.$body.removeAttr("data-layout");
	}

	reset_chrome() {
		this.page.clear_primary_action();
		this.page.clear_secondary_action();
		this.page.clear_menu();
		this.page.clear_indicator();
		this.page.clear_custom_actions();
		this.page.set_breadcrumbs([]);
	}

	show_overview() {
		const request_id = ++this.request_id;
		this.reset_chrome();
		this.$body.attr("data-view", "overview");
		this.page.set_title(__("Hiring pipeline"));
		this.page.set_primary_action(
			__("New opening"),
			() => frappe.new_doc("Job Opening"),
			"plus",
		);

		hrms.hiring.clear(this.$body).append(skeleton_overview());
		frappe.call({ method: "hrms.hr.page.hiring.overview.get_overview", type: "GET" }).then((r) => {
			if (request_id !== this.request_id) return;
			this.render_overview(r.message);
		});
	}

	render_overview({ openings }) {
		hrms.hiring.clear(this.$body).append(this.make_openings_section(openings));
	}

	make_openings_section(openings) {
		const open = openings.filter((opening) => opening.status === "Open");
		// a closed opening stays in view while candidates are still interviewing or holding an offer
		const is_live = (opening) => opening.status === "Open" || opening.active > 0;
		const listed = openings.filter(is_live);
		const closed = openings.filter((opening) => !is_live(opening));
		const toolbar = openings.length
			? new hrms.hiring.OverviewToolbar(openings, this.overview_filter, () => render_lists())
			: null;
		const $listed = $(`<div></div>`);
		const $closed = $(`<div></div>`);
		let is_closed_open = false;
		const render_lists = () => {
			const matches = (opening) => !toolbar || toolbar.matches(opening);
			const arrange = (rows) => (toolbar ? toolbar.sort(rows.filter(matches)) : rows);
			const empty = this.get_empty(openings, toolbar);
			const list = this.make_openings_list(arrange(listed), { empty });
			$listed.empty().append(list.$el);
			$closed.empty();
			const matching_closed = arrange(closed);
			if (!matching_closed.length) return;
			const toggle = this.make_closed_toggle(matching_closed, is_closed_open);
			toggle.on_toggle = (is_open) => (is_closed_open = is_open);
			$closed.append(toggle.$el);
		};
		const $section = $(`<section class="hiring__section"></section>`).append(
			make_heading(__("Openings"), open.length),
			listed.length
				? $(`<p class="hiring__hint text-p-base"></p>`).text(
						__("Select an opening to see its pipeline.")
				  )
				: null,
			toolbar?.$el,
			$listed,
		);
		render_lists();
		return $section.append($closed);
	}

	get_empty(openings, toolbar) {
		if (!openings.length) {
			return {
				title: __("No openings yet"),
				description: __("Create an opening to start taking applications."),
				actions: [
					{
						label: __("New opening"),
						variant: "subtle",
						onclick: () => frappe.new_doc("Job Opening"),
					},
				],
			};
		}
		if (!toolbar.has_filters) return { title: __("Nothing is open right now") };
		return {
			title: __("No openings match"),
			actions: [{ label: __("Clear filters"), variant: "subtle", onclick: () => toolbar.clear_filters() }],
		};
	}

	make_closed_toggle(closed, is_expanded = false) {
		const list = this.make_openings_list(closed, { css_class: "hiring__closed" });
		const get_look = (is_open) => ({
			label: is_open ? __("Hide closed") : __("Show closed"),
			icon_right: is_open ? "chevron-up" : "chevron-down",
			variant: "ghost",
		});
		list.$el.toggle(is_expanded);
		const handle = {};
		const $toggle = frappe.ui
			.button({
				...get_look(is_expanded),
				onclick: () => {
					const is_hidden = list.$el.is(":hidden");
					list.$el.toggle(is_hidden);
					frappe.ui.button.dress($toggle, get_look(is_hidden));
					handle.on_toggle?.(is_hidden);
				},
			})
			.addClass("hiring__toggle");
		handle.$el = $(`<div></div>`).append($toggle, list.$el);
		return handle;
	}

	get_opening_item(opening) {
		const is_open = opening.status === "Open";
		const subtitle = [opening.department, opening.location].filter(Boolean).join(" · ");
		return {
			id: opening.name,
			title: opening.job_title,
			subtitle: subtitle || __("No department or location"),
			meta: opening.needs_you?.label,
			badge: is_open ? this.get_closing_badge(opening) : { label: __("Closed") },
			href: frappe.router.make_url(
				hrms.hiring.get_pipeline_route(opening.name, opening.attention_stage),
			),
		};
	}

	/** An openings list; the faint placeholder subtitle and the late tint are marked on the rendered rows. */
	make_openings_list(openings, opts = {}) {
		const list = new frappe.ui.ItemList({
			...opts,
			items: openings.map((opening) => this.get_opening_item(opening)),
		});
		for (const opening of openings) {
			const row = list.rows.get(opening.name);
			if (!opening.department && !opening.location) {
				row.querySelector(".es-item-list__subtitle")?.setAttribute("data-faint", "");
			}
			const meta = row.querySelector(".es-item-list__meta");
			meta?.toggleAttribute("data-late", Boolean(opening.needs_you.is_late));
		}
		return list;
	}

	get_closing_badge(opening) {
		if (!opening.closes_on) return null;
		const days = frappe.datetime.get_day_diff(opening.closes_on, frappe.datetime.get_today());
		if (days < 0 || days > hrms.hiring.CLOSING_SOON_DAYS) return null;
		return { label: hrms.hiring.get_closing_label(days), theme: "amber" };
	}

	/** `slug`: the stage as the URL spells it, lowercase; none lands on the first stage with applicants. */
	show_opening(opening, slug, applicant) {
		const match = STAGES.find((stage) => stage.toLowerCase() === slug?.toLowerCase());
		const stage = match || "Applied";
		if (this.opening_view?.name === opening) return this.opening_view.show(stage, applicant);
		this.leave_opening();
		this.request_id++;
		this.reset_chrome();
		hrms.hiring.clear(this.$body).attr("data-view", "opening");
		this.opening_view = new hrms.hiring.OpeningView(this, opening, stage, applicant, !match);
		return false;
	}
};

{% include "hrms/hr/page/hiring/overview_toolbar.js" %}
{% include "hrms/hr/page/hiring/opening_view.js" %}
{% include "hrms/hr/page/hiring/applicant_composer.js" %}
{% include "hrms/hr/page/hiring/applicant_thread.js" %}
{% include "hrms/hr/page/hiring/applicant_mail.js" %}
{% include "hrms/hr/page/hiring/applicant_comments.js" %}
{% include "hrms/hr/page/hiring/applicant_decisions.js" %}
{% include "hrms/hr/page/hiring/applicant_panel.js" %}
