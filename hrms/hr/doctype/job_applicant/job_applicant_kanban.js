frappe.provide("frappe.kanban_v2.settings");

// opened from an opening, the board shows that opening's title and status
frappe.kanban_v2.settings["Job Applicant"] = {
	hide_empty_fields: true,
	boards: {
		// a drop onto a stage that needs a record opens the step that creates it
		"Hiring Pipeline": { callbacks: { onBeforeCardMove: before_hiring_move } },
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
				method: "hrms.hr.doctype.job_opening.job_opening.get_opening_header",
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

// only these stages are a plain save, so only these take several cards at once
const BULK_MOVE_STAGES = ["Applied", "Shortlisted"];

// a step that did the move itself (scheduled, offered, rejected) reloads the board instead of saving
async function before_hiring_move(move, page) {
	if (move.cardIds.length > 1) {
		if (BULK_MOVE_STAGES.includes(move.toColumn)) return true;
		frappe.msgprint(__("Move one applicant at a time to {0}", [__(move.toColumn)]));
		return false;
	}
	const applicant = {
		name: move.cardId,
		applicant_name: move.title || move.cardId,
		designation: move.doc?.designation,
	};
	const outcome = await hrms.hiring
		.move_to_stage(applicant, move.toColumn, { on_undo: () => page.board?.refresh() })
		.catch(() => "cancel");
	if (outcome === "done") page.board?.refresh();
	return outcome === "move";
}
