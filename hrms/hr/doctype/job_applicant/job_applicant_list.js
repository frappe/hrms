// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

frappe.listview_settings["Job Applicant"] = {
	add_fields: ["status", "applicant_rating", "designation"],

	onload: function () {
		patch_kanban_dialog_for_job_applicant();
	},

	get_indicator: function (doc) {
		if (doc.status === "Accepted") {
			return [__(doc.status), "green", "status,=," + doc.status];
		} else if (doc.status === "Shortlisted") {
			return [__(doc.status), "blue", "status,=," + doc.status];
		} else if (["Open", "Replied"].includes(doc.status)) {
			return [__(doc.status), "orange", "status,=," + doc.status];
		} else if (["Hold", "Rejected"].includes(doc.status)) {
			return [__(doc.status), "red", "status,=," + doc.status];
		}
	},
};

// Replaces the inline textarea UX with a direct frappe.new_doc() call so the
// status of the column is pre-filled and the user lands straight on the form.
document.addEventListener(
	"click",
	function (e) {
		const add_card_btn = e.target.closest(".kanban .add-card");
		if (!add_card_btn) return;

		const route = frappe.get_route();
		if (route[0] !== "List" || route[1] !== "Job Applicant" || route[2] !== "Kanban") return;

		e.stopImmediatePropagation();
		e.preventDefault();

		const column_title = add_card_btn.closest(".kanban-column").dataset.columnValue;
		frappe.new_doc("Job Applicant", { status: column_title });
	},
	true, // capture phase
);

// Allow rating stars to be clicked directly on kanban cards.
// Clicking the same value again toggles the rating back to 0 (matches desk behaviour).
document.addEventListener("click", function (e) {
	const star_svg = e.target.closest(".kanban .kanban-card-doc .rating svg");
	if (!star_svg) return;

	const route = frappe.get_route();
	if (route[0] !== "List" || route[1] !== "Job Applicant" || route[2] !== "Kanban") return;

	e.stopPropagation();

	const OUT_OF = 5;
	const star_index = parseInt(star_svg.getAttribute("data-rating"), 10);
	const rect = star_svg.getBoundingClientRect();
	const is_left_half = e.clientX - rect.left < rect.width / 2;
	const clicked_fraction = (is_left_half ? star_index - 0.5 : star_index) / OUT_OF;

	const card_wrapper = star_svg.closest(".kanban-card-wrapper");
	if (!card_wrapper) return;
	const docname = decodeURIComponent(card_wrapper.dataset.name);

	const rating_el = star_svg.closest(".rating");
	const current_fraction = kanban_rating_from_stars(rating_el, OUT_OF);
	const new_fraction = current_fraction === clicked_fraction ? 0 : clicked_fraction;

	frappe.db
		.set_value("Job Applicant", docname, "applicant_rating", new_fraction)
		.then(() => {
			kanban_apply_stars(rating_el, new_fraction, OUT_OF);
		})
		.catch(() => {
			kanban_apply_stars(rating_el, current_fraction, OUT_OF);
		});
});

function kanban_rating_from_stars(rating_el, out_of) {
	let value = 0;
	rating_el.querySelectorAll("svg").forEach((svg, i) => {
		const has_left = svg.querySelector(".left-half").classList.contains("star-click");
		const has_right = svg.querySelector(".right-half").classList.contains("star-click");
		if (has_left && has_right) value = (i + 1) / out_of;
		else if (has_left) value = (i + 0.5) / out_of;
	});
	return value;
}

function kanban_apply_stars(rating_el, fraction, out_of) {
	const filled = fraction * out_of;
	rating_el.querySelectorAll("svg").forEach((svg, i) => {
		const n = i + 1;
		const left = svg.querySelector(".left-half");
		const right = svg.querySelector(".right-half");
		if (n <= filled && filled % 1 === 0) {
			left.classList.add("star-click");
			right.classList.add("star-click");
		} else if (n <= Math.floor(filled)) {
			left.classList.add("star-click");
			right.classList.add("star-click");
		} else if (n - 0.5 <= filled) {
			left.classList.add("star-click");
			right.classList.remove("star-click");
		} else {
			left.classList.remove("star-click");
			right.classList.remove("star-click");
		}
	});
}

function patch_kanban_dialog_for_job_applicant() {
	if (frappe.views.KanbanView._job_applicant_kanban_patched) return;

	const _original = frappe.views.KanbanView.show_kanban_dialog;
	frappe.views.KanbanView.show_kanban_dialog = function (doctype) {
		if (doctype !== "Job Applicant") {
			return _original.call(this, doctype);
		}
		frappe
			.xcall("hrms.hr.doctype.job_applicant.job_applicant.create_kanban_board", {
				board_name: "Hiring Pipeline",
			})
			.then((board) => {
				frappe.set_route("List", "Job Applicant", "Kanban", board.kanban_board_name);
			});
	};

	frappe.views.KanbanView._job_applicant_kanban_patched = true;
}
