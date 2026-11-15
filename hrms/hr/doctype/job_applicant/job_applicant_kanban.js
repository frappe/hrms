frappe.provide("frappe.kanban_v2.settings");

// opened from an opening, the board shows that opening's title and status
frappe.kanban_v2.settings["Job Applicant"] = {
	hide_empty_fields: true,
	boards: {
		// a drop onto a stage that needs a record opens the step that creates it
		"Hiring Pipeline": { before_move: before_hiring_move },
	},

	setup_page(board) {
		const page = board.page;
		const filter = board
			.get_effective_filters()
			.find(([, field, operator]) => field === "job_title" && operator === "=");
		page.clear_secondary_action();
		page.clear_indicator();
		if (!filter) {
			page.set_breadcrumbs(page.get_breadcrumbs().slice(-1));
			return board.views_list?.refresh_trigger();
		}
		frappe
			.call({
				method: "hrms.hr.page.hiring.hiring.get_opening_header",
				type: "GET",
				args: { job_opening: filter[3] },
			})
			.then((response) => show_opening_header(board, response.message));
	},
};

function show_opening_header(board, opening) {
	const page = board.page;
	const is_open = opening.status === "Open";
	page.clear_primary_action();
	page.set_title(opening.display_title);
	page.set_indicator(is_open ? __("Open") : __("Closed"), is_open ? "green" : "gray");
	board.views_list?.set_trigger_content(frappe.views.get_view_label_map().Kanban);
	if (!is_open) return;
	page.set_secondary_action(
		__("Add applicant"),
		() =>
			frappe.new_doc("Job Applicant", {
				job_title: opening.name,
				designation: opening.designation,
			}),
		"plus",
	);
}

function before_hiring_move({ name, title, to, doc }) {
	const applicant = { name, applicant_name: title || name, designation: doc?.designation };
	return hrms.hiring.move_to_stage(applicant, to, { on_undo: () => cur_list?.refresh?.() });
}
