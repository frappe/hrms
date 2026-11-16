const API = "hrms.hr.page.hiring.overview.get_overview";
const MAX_CARDS = 6;
const SKELETON_CARDS = 3;
const el = hrms.hiring.make_element;

function skeleton(width, height) {
	return frappe.ui.skeleton({ width, height })[0];
}

function closing_meta(opening) {
	if (!opening.closes_on) return null;
	const days = frappe.datetime.get_day_diff(opening.closes_on, frappe.datetime.get_today());
	if (days < 0) return { label: __("Past closing date"), soon: true };
	return {
		label: hrms.hiring.get_closing_label(days),
		soon: days <= hrms.hiring.CLOSING_SOON_DAYS,
	};
}

function pipeline_href(opening, stage) {
	return frappe.router.make_url(hrms.hiring.get_pipeline_route(opening.name, stage));
}

function is_filled(opening) {
	return opening.vacancies > 0 && opening.hired >= opening.vacancies;
}

function badge(opening) {
	if (is_filled(opening)) return frappe.ui.badge({ label: __("Filled") })[0];
	const closing = closing_meta(opening);
	return closing?.soon && frappe.ui.badge({ label: closing.label, theme: "amber" })[0];
}

function progress_text(opening) {
	if (opening.vacancies > 0)
		return el("span", { text: __("{0} of {1} hired", [opening.hired, opening.vacancies]) });
	return el(
		"span",
		{},
		`${__("{0} hired", [opening.hired])} · `,
		el("span", { class: "faint", text: __("no target") }),
	);
}

// the one thing worth saying about the role comes from the API (opening.needs_you)
function make_item(opening) {
	const stuck = opening.needs_you;
	if (stuck && stuck.kind === "offers_out")
		return el("span", { class: "overdue text-p-sm-medium", text: stuck.label });
	if (stuck) {
		return el("a", {
			class: stuck.is_late ? "item overdue text-p-sm-medium" : "item text-p-sm-medium",
			href: pipeline_href(opening, stuck.stage),
			text: stuck.label,
		});
	}
	if (!opening.applicants) return el("span", { text: __("No applicants yet") });
	return el("span", {
		text:
			opening.applicants === 1
				? __("{0} applicant", [opening.applicants])
				: __("{0} applicants", [opening.applicants]),
	});
}

function make_card(opening, show_location) {
	const title =
		show_location && opening.location
			? `${opening.job_title} · ${opening.location}`
			: opening.job_title;
	return el(
		"div",
		{ class: "role" },
		el(
			"div",
			{ class: "top" },
			el("a", {
				class: "name text-p-base-medium",
				href: pipeline_href(opening, opening.attention_stage),
				text: title,
				title,
			}),
			badge(opening),
		),
		el("div", { class: "sub text-p-sm" }, progress_text(opening), " · ", make_item(opening)),
	);
}

function make_skeleton_card() {
	return el(
		"div",
		{ class: "role", "aria-hidden": "true" },
		el("div", { class: "top" }, skeleton("55%", "14px")),
		el("div", { class: "sub text-p-sm" }, skeleton("80%", "12px")),
	);
}

function make_empty() {
	return el(
		"div",
		{ class: "empty text-base" },
		el("span", { class: "empty-title text-base-medium", text: __("No open roles") }),
		el("a", {
			class: "create text-base",
			href: "/desk/job-opening/new",
			text: __("Create job opening"),
		}),
	);
}

const host = root_element.querySelector("[data-root]");
const count_label = el("span", { class: "count text-base" });
const grid = el("div", { class: "grid" });
host.append(
	el(
		"div",
		{ class: "head" },
		el("h2", { class: "title text-base-semibold" }, __("Open roles"), count_label),
		el("a", { class: "view-all text-p-sm", href: "/desk/hiring", text: __("View all") }),
	),
	grid,
);

function show(content) {
	grid.replaceChildren(...content);
}

hrms.hiring.route_block_links(root_element);

function load() {
	show(Array.from({ length: SKELETON_CARDS }, make_skeleton_card));
	frappe
		.call({ method: API, type: "GET", silent: true })
		.then((response) => {
			const open = response.message.openings.filter((opening) => opening.status === "Open");
			count_label.textContent = open.length || "";
			if (!open.length) {
				grid.removeAttribute("class");
				return show([make_empty()]);
			}
			const shown = open.slice(0, MAX_CARDS);
			const titles = shown.map((opening) => opening.job_title);
			show(
				shown.map((opening) =>
					make_card(opening, titles.filter((t) => t === opening.job_title).length > 1),
				),
			);
		})
		.catch(() => {
			grid.removeAttribute("class");
			show([
				el("div", {
					class: "empty text-base",
					text: __("Open roles could not be loaded"),
				}),
			]);
		});
}

// people without access to applicants (interviewers) have nothing here
if (frappe.model.can_read("Job Applicant")) load();
else hrms.hiring.hide_block(root_element);
