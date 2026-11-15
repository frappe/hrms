const API = "hrms.hr.page.hiring.hiring.get_upcoming_interviews";
const DAYS = 7;
const SKELETON_ROWS = 3;
const el = hrms.hiring.make_element;

function day_label(date) {
	const today = frappe.datetime.get_today();
	if (date === today) return __("Today");
	if (date === frappe.datetime.add_days(today, 1)) return __("Tomorrow");
	return moment(date).format("ddd D MMM");
}

function format_time(time) {
	return time ? moment(time, "HH:mm:ss").format("LT") : "–";
}

function interview_href(interview) {
	// an applicant with no opening has no Hiring page to land on
	if (!interview.job_opening)
		return `/desk/job-applicant/${encodeURIComponent(interview.job_applicant)}`;
	return ["/desk/hiring", interview.job_opening, interview.stage, interview.job_applicant]
		.map((part, index) => (index ? encodeURIComponent(part) : part))
		.join("/");
}

// the same row list as the hiring openings list; a missing panel is the one thing to flag
function get_item(interview) {
	return {
		id: interview.name,
		title: interview.applicant_name,
		subtitle: [interview.interview_type, interview.opening_title].filter(Boolean).join(" · "),
		meta: [day_label(interview.scheduled_on), format_time(interview.from_time)].join(", "),
		avatar: { label: interview.applicant_name },
		badge: interview.panel.length ? null : { label: __("No interviewers"), theme: "amber" },
		href: interview_href(interview),
	};
}

function make_list(interviews) {
	return new frappe.ui.ItemList({ items: interviews.map(get_item) }).el;
}

function make_skeleton() {
	const bar = (width, height) => frappe.ui.skeleton.html({ width, height });
	const row = `<div class="es-item-list__row" data-avatar>
		<span class="es-item-list__lead">${frappe.ui.skeleton.html({
			width: "20px",
			height: "20px",
			css_class: "skeleton-avatar",
		})}</span>
		<span class="es-item-list__text">
			<span class="es-item-list__title">${bar("40%", "12px")}</span>
			<span class="es-item-list__subtitle">${bar("30%", "10px")}</span>
		</span>
		<span class="es-item-list__meta">${bar("96px", "10px")}</span>
	</div>`;
	const box = el("div", { class: "es-item-list", "aria-hidden": "true" });
	box.innerHTML = row.repeat(SKELETON_ROWS);
	return box;
}

function view_all() {
	frappe.set_route("List", "Interview", { scheduled_on: [">=", frappe.datetime.get_today()] });
}

const host = root_element.querySelector("[data-root]");
const count_label = el("span", { class: "count text-base" });
const content = el("div", { class: "content" });
const view_all_link = el("a", {
	class: "view-all text-p-sm",
	href: "/desk/interview",
	"data-view-all": true,
	text: __("View all"),
});
host.append(
	el(
		"div",
		{ class: "head" },
		el("h2", { class: "title text-base-semibold" }, __("Upcoming interviews"), count_label),
		view_all_link,
	),
	content,
);

function show(nodes) {
	content.replaceChildren(...nodes);
}

hrms.hiring.route_block_links(root_element, (link) => {
	if (!link.hasAttribute("data-view-all")) return false;
	view_all();
	return true;
});

function load() {
	show([make_skeleton()]);
	frappe
		.call({ method: API, type: "GET", args: { days: DAYS }, silent: true })
		.then((response) => {
			const { count, interviews } = response.message;
			count_label.textContent = count || "";
			if (!interviews.length) {
				hrms.hiring.hide_block(root_element);
				return show([
					el("div", {
						class: "empty text-base",
						text: __("No interviews in the next {0} days", [DAYS]),
					}),
				]);
			}
			const nodes = [make_list(interviews)];
			if (count > interviews.length) {
				nodes.push(
					el("a", {
						class: "more-link text-p-sm",
						href: "/desk/interview",
						"data-view-all": true,
						text: __("+{0} more", [count - interviews.length]),
					}),
				);
			}
			show(nodes);
		})
		.catch(() =>
			show([
				el("div", {
					class: "empty text-base",
					text: __("Upcoming interviews could not be loaded"),
				}),
			]),
		);
}

// people without access to applicants (interviewers) have nothing here
if (frappe.model.can_read("Job Applicant")) load();
else hrms.hiring.hide_block(root_element);
