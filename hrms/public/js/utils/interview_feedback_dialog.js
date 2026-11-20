frappe.provide("hrms");

/** Opens the dialog where an interviewer rates the skills, picks a result and submits feedback. */
hrms.open_interview_feedback = ({ interview, skills, on_submitted }) =>
	new InterviewFeedbackDialog(interview, skills, on_submitted).show();

class InterviewFeedbackDialog {
	constructor(interview, skills, on_submitted) {
		this.interview = interview;
		this.skill_names = (skills || []).map((row) => row.skill);
		this.on_submitted = on_submitted;
		this.rating_controls = [];
		this.result = "";
		this.make();
	}

	make() {
		this.dialog = new frappe.ui.Dialog({
			title: __("Interview Feedback"),
			fields: [{ fieldname: "body", fieldtype: "HTML" }],
			static: true,
			primary_action_label: __("Submit feedback"),
			primary_action: () => this.submit(),
		});
		this.dialog.$wrapper.addClass("interview-feedback-dialog");
		// static keeps a stray outside click from wiping the form; Esc still closes, like other dialogs
		this.dialog.$wrapper.on("keydown", (e) => e.key === "Escape" && this.dialog.hide());

		this.$body = $(this.body_html()).appendTo(this.dialog.fields_dict.body.$wrapper.empty());
		this.$notes = this.$body.find("textarea");
		this.$notes.attr(
			"placeholder",
			__("What stood out? Anything the next interviewer should probe?"),
		);

		this.skill_names.forEach((skill, i) => this.render_skill(skill, i));
		this.render_results();
	}

	show() {
		this.dialog.show();
		this.dialog.get_close_btn().show();
		this.$body.find(".ifd-error").hide();
	}

	body_html() {
		return `
			<div class="ifd">
				${this.header_html()}
				${
					this.skill_names.length
						? '<section class="ifd-skills"><p class="ifd-error text-p-sm" data-error="skills"></p><div class="ifd-grid"></div></section>'
						: ""
				}
				<section>
					<div class="ifd-results" role="group"></div>
					<p class="ifd-error text-p-sm" data-error="result"></p>
				</section>
				<section class="ifd-notes">
					<label class="ifd-label text-p-base-medium" for="ifd-feedback">${__("Feedback")}</label>
					<textarea id="ifd-feedback" class="form-control" rows="3"></textarea>
				</section>
			</div>`;
	}

	header_html() {
		const doc = this.interview;
		const when = doc.scheduled_on ? frappe.datetime.str_to_user(doc.scheduled_on) : "";
		const date = doc.scheduled_on ? moment(doc.scheduled_on).format("D MMM") : "";
		const line = [doc.interview_type, doc.designation, date].filter(Boolean).join(" · ");
		const escape = frappe.utils.escape_html;
		return `<span class="ifd-header">
			${frappe.ui.avatar.html({ label: doc.applicant_name, size: "xl", theme: "auto", title: when })}
			<span class="ifd-header__text">
				<span class="ifd-header__name text-p-base-medium">${escape(doc.applicant_name || "")}</span>
				${line ? `<span class="ifd-header__line text-p-base">${escape(line)}</span>` : ""}
			</span>
		</span>`;
	}

	render_skill(skill, i) {
		const meanings = [__("Poor"), __("Fair"), __("Good"), __("Strong"), __("Exceptional")];
		const $cell = $(
			'<div class="ifd-skill"><p class="ifd-skill__name text-p-sm"></p><div class="ifd-skill__stars"></div></div>',
		);
		$cell.find(".ifd-skill__name").text(skill);
		$cell.appendTo(this.$body.find(".ifd-grid"));
		const $stars = $cell.find(".ifd-skill__stars");
		const control = frappe.ui.form.make_control({
			df: { fieldtype: "Rating", fieldname: `rating_${i}`, label: skill, options: 5 },
			parent: $stars,
			render_input: true,
		});
		this.rating_controls.push(control);
		$stars.find(".control-label, .help-box").remove();
		const tooltip = frappe.ui.tooltip($stars, { text: " ", delay: 200 }).data("es-tooltip");
		$stars.find("svg").each(function (index) {
			$(this).on("mouseenter", () => tooltip.set_text(meanings[index]));
		});
		$stars.on("click", () => this.clear_error("skills"));
	}

	render_results() {
		this.$results = this.$body.find(".ifd-results");
		[
			{ value: "Cleared", label: __("Cleared"), icon: "thumbs-up" },
			{ value: "Rejected", label: __("Rejected"), icon: "thumbs-down" },
		].forEach((option) => {
			frappe.ui
				.button({
					label: option.label,
					icon_left: option.icon,
					variant: "outline",
					css_class: "ifd-result",
					attrs: { "aria-pressed": "false", "data-result": option.value },
					onclick: () => {
						this.result = option.value;
						this.clear_error("result");
						this.paint_results();
					},
				})
				.appendTo(this.$results);
		});
	}

	paint_results() {
		const result = this.result;
		this.$results.find(".ifd-result").each(function () {
			const picked = $(this).data("result") === result;
			$(this).attr("aria-pressed", picked);
			$(this).attr("data-variant", picked ? "subtle" : "outline");
		});
	}

	show_error(key, message) {
		this.$body.find(`[data-error=${key}]`).text(message).show();
	}

	clear_error(key) {
		this.$body.find(`[data-error=${key}]`).text("").hide();
	}

	set_busy(busy) {
		this.$notes.prop("disabled", busy);
		this.$body.find(".ifd-result").prop("disabled", busy);
		this.$body.find(".ifd-skill__stars").toggleClass("is-disabled", busy);
		this.dialog.get_primary_btn().attr("aria-busy", busy ? "true" : null);
		busy ? this.dialog.disable_primary_action() : this.dialog.enable_primary_action();
	}

	is_valid() {
		const unrated = this.rating_controls.some((control) => !flt(control.get_value()));
		unrated ? this.show_error("skills", __("Rate every skill")) : this.clear_error("skills");
		this.result ? this.clear_error("result") : this.show_error("result", __("Pick a result"));
		return !unrated && Boolean(this.result);
	}

	submit() {
		if (!this.is_valid()) return;

		this.set_busy(true);
		return frappe
			.xcall("hrms.hr.doctype.interview.interview.create_interview_feedback", {
				data: {
					skill_set: this.skill_names.map((skill, i) => ({
						skill,
						rating: this.rating_controls[i].get_value(),
					})),
					result: this.result,
					feedback: this.$notes.val(),
				},
				interview_name: this.interview.name,
				interviewer: frappe.session.user,
				job_applicant: this.interview.job_applicant,
			})
			.then(() => {
				this.dialog.hide();
				frappe.ui.toast({ message: __("Feedback submitted"), type: "success" });
				this.on_submitted?.();
			})
			.catch(() => this.set_busy(false));
	}
}
