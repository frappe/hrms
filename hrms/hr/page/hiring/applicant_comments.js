const COMMENT_API = "frappe.desk.form.utils.add_comment";
const COMMENT_GROUP_MINUTES = 10;

// Unsent comments, kept per applicant like reply drafts.
const comment_drafts = new Map();

/** Only paragraphs and line breaks: the panel's plain-text editor can't keep anything richer. */
function is_plain_comment(html) {
	const tags = html.match(/<\/?[a-z][a-z\d]*/gi) || [];
	return tags.every((tag) => /^<\/?(p|br|div)$/i.test(tag));
}

/** The Comments tab of the applicant panel: what only the team reads. `reload` refreshes the whole panel. */
hrms.hiring.ApplicantComments = class ApplicantComments {
	constructor({ data, reload }) {
		this.data = data;
		this.reload = reload;
		this.nodes = this.make_comments_tab();
	}

	make_comments_tab() {
		const { comments } = this.data;
		// no empty state: "Team only" and the box's placeholder already say who sees comments
		if (!comments.length) return this.make_comment_box();
		return [
			$(`<ul class="hiring__comments"></ul>`).append(this.make_comment_items(comments)),
			this.make_comment_box(),
		];
	}

	/** Comments as list items: a day divider when the day changes, and a new head unless the same person is still going. */
	make_comment_items(comments) {
		const items = [];
		let previous = null;
		for (const comment of comments) {
			const day = moment(comment.creation).startOf("day");
			const is_new_day = previous
				? !day.isSame(moment(previous.creation), "day")
				: day.isBefore(moment().startOf("day"));
			if (is_new_day) items.push(this.make_day_divider(day));
			const is_continued =
				previous &&
				!is_new_day &&
				previous.comment_email === comment.comment_email &&
				moment(comment.creation).diff(moment(previous.creation), "minutes", true) <=
					COMMENT_GROUP_MINUTES;
			items.push(this.make_comment(comment, is_continued));
			previous = comment;
		}
		return items;
	}

	make_day_divider(day) {
		const today = moment().startOf("day");
		let label = day.format(day.year() === today.year() ? "D MMM" : "D MMM YYYY");
		if (day.isSame(today)) label = __("Today");
		else if (day.isSame(today.clone().subtract(1, "day"))) label = __("Yesterday");
		return $(`<li class="hiring__comment-day text-p-sm" role="separator"></li>`).text(label);
	}

	make_comment(comment, is_continued) {
		const is_mine = comment.comment_email === frappe.session.user;
		const author = comment.comment_by || comment.comment_email;
		const name = is_mine ? __("You") : author;
		const $text = $(`<div class="hiring__comment-text text-p-base"></div>`).html(
			comment.content,
		);
		const $item = $(`<li class="hiring__comment"></li>`).attr(
			"data-continued",
			is_continued ? "" : null,
		);
		if (is_continued) {
			$text.attr("title", frappe.datetime.str_to_user(comment.creation));
		} else {
			$item.append(
				$(`<div class="hiring__comment-head text-p-base"></div>`).append(
					frappe.ui.avatar({ label: author, size: "sm", theme: "auto" }),
					$(`<strong class="hiring__comment-name text-p-base-medium"></strong>`).text(
						name,
					),
					$(`<span class="hiring__comment-time text-p-sm"></span>`)
						.text(ago(comment.creation))
						.attr("title", frappe.datetime.str_to_user(comment.creation)),
				),
			);
		}
		$item.append($text);
		if (is_mine) $item.append(this.make_comment_menu(comment, $text));
		return $item;
	}

	make_comment_menu(comment, $text) {
		return frappe.ui
			.dropdown({
				button: {
					icon: "ellipsis",
					variant: "ghost",
					size: "sm",
					css_class: "hiring__comment-menu",
					attrs: { "aria-label": __("Comment actions") },
				},
				align: "end",
				options: [
					{
						label: __("Edit"),
						icon: "pencil",
						// formatting, links, mentions and images only survive an edit in the form
						onclick: () =>
							is_plain_comment(comment.content)
								? this.edit_comment(comment, $text)
								: frappe.set_route("Form", "Job Applicant", this.data.name),
					},
					{
						label: __("Delete"),
						icon: "trash-2",
						theme: "red",
						onclick: () => this.confirm_delete_comment(comment),
					},
				],
			})
			.addClass("hiring__comment-menu");
	}

	/** Swaps the body for a textarea with the comment's plain text. Saving reloads; cancelling puts the body back. */
	edit_comment(comment, $text) {
		const $item = $text.closest(".hiring__comment");
		const close = () => {
			composer.$el.remove();
			$item.removeAttr("data-editing");
			$text.show();
		};
		const composer = hrms.hiring.make_composer({
			label: __("Edit comment"),
			value: hrms.hiring.html_to_text(comment.content),
			submit: { label: __("Save") },
			on_submit: (text) => this.update_comment(comment, text),
			end: [
				frappe.ui.button({
					label: __("Cancel"),
					variant: "ghost",
					size: "sm",
					onclick: () => close(),
				}),
			],
			on_escape: () => close(),
		});
		$text.hide().after(composer.$el.addClass("hiring__comment-editor"));
		$item.attr("data-editing", "");
		const input = composer.$input[0];
		input.focus();
		input.setSelectionRange(input.value.length, input.value.length);
	}

	update_comment(comment, text) {
		return frappe
			.xcall("frappe.desk.form.utils.update_comment", {
				name: comment.name,
				content: escape_to_html(text.trim()),
			})
			.then(() => this.reload());
	}

	confirm_delete_comment(comment) {
		hrms.hiring.open_confirm_dialog({
			title: __("Delete this comment?"),
			body: `<p>${frappe.utils.escape_html(__("This can't be undone."))}</p>`,
			primary_label: __("Delete"),
			theme: "red",
			on_confirm: async () => {
				await frappe.xcall("frappe.client.delete", {
					doctype: "Comment",
					name: comment.name,
				});
				frappe.ui.toast({ message: __("Comment deleted") });
				this.reload();
			},
		});
	}

	make_comment_box() {
		return hrms.hiring.make_composer({
			placeholder: __("Add a comment for the hiring team"),
			label: __("Comment"),
			drafts: comment_drafts,
			draft_key: this.data.name,
			submit: { label: __("Comment") },
			on_submit: (text) => this.add_comment(text),
		}).$el;
	}

	add_comment(text) {
		const { name } = this.data;
		if (!text.trim()) return Promise.resolve();
		return frappe
			.xcall(COMMENT_API, {
				reference_doctype: "Job Applicant",
				reference_name: name,
				content: escape_to_html(text.trim()),
				comment_email: frappe.session.user,
				comment_by: frappe.session.user_fullname,
			})
			.then(() => {
				comment_drafts.delete(name);
				this.reload();
			});
	}
};
