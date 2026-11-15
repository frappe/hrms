/**
 * Deciding interviews and recording offer answers from the applicant panel.
 *
 * Status changes save the draft with an Undo. Picking a result (Cleared or Rejected) asks first, then
 * submits; a submitted interview can still switch between the two results.
 */

const DECIDED_INTERVIEW_STATUSES = ["Cleared", "Rejected"];
// the doctype's order; Cancelled sits apart, under a divider
const INTERVIEW_STATUS_MENU = ["Pending", "Under Review", "Cleared", "Rejected", "Cancelled"];

const escape_html = frappe.utils.escape_html;

hrms.hiring.ApplicantDecisions = class ApplicantDecisions {
	/** @param {hrms.hiring.ApplicantPanel} panel */
	constructor(panel) {
		this.panel = panel;
	}

	get view() {
		return this.panel.view;
	}

	/** What the ItemList `controls` slot holds at the right end of an interview row: a status dropdown while it's a draft, else a plain badge. */
	make_interview_controls(interview, data) {
		const { label, theme } = hrms.hiring.get_interview_badge(interview);
		const is_submitted_result =
			interview.docstatus === 1 && DECIDED_INTERVIEW_STATUSES.includes(interview.status);
		if (is_submitted_result) return this.make_result_switch(interview, data);
		if (interview.docstatus !== 0) return frappe.ui.badge({ label, theme });

		const dropdown = this.make_status_dropdown({
			label,
			aria_label: __("{0} status: {1}", [interview.interview_type, label]),
			options: INTERVIEW_STATUS_MENU.map((status) => {
				const is_result = DECIDED_INTERVIEW_STATUSES.includes(status);
				return {
					label: hrms.hiring.get_interview_status_label(status),
					selected: status === interview.status,
					// a draft saved as Cleared or Rejected (before results submitted themselves) can still be submitted
					allow_current: is_result,
					divider_before: status === "Cancelled",
					run: () =>
						is_result
							? this.confirm_result(interview, data, status)
							: this.set_result(interview, data, status),
				};
			}),
		});
		// the menu leads, so statuses line up on the right edge down the list
		return [this.make_reschedule_menu(interview, data), dropdown];
	}

	/** A submitted interview keeps its result editable, but only between Cleared and Rejected; switching has an Undo. */
	make_result_switch(interview, data) {
		const label = hrms.hiring.get_interview_status_label(interview.status);
		return this.make_status_dropdown({
			label,
			aria_label: __("{0} status: {1}", [interview.interview_type, label]),
			options: DECIDED_INTERVIEW_STATUSES.map((status) => ({
				label: hrms.hiring.get_interview_status_label(status),
				selected: status === interview.status,
				run: async () => {
					await this.set_result(interview, data, status);
					if (status === "Rejected" && data.stage !== "Rejected")
						this.offer_to_reject(data);
				},
			})),
		});
	}

	/** A pending interview that hasn't happened yet can be moved, as from its form; it's rare, so it sits in a ⋯ menu. */
	make_reschedule_menu(interview, data) {
		const is_upcoming = interview.scheduled_on >= frappe.datetime.get_today();
		if (interview.status !== "Pending" || !is_upcoming) return null;
		return frappe.ui.dropdown({
			button: {
				icon: "ellipsis",
				variant: "ghost",
				size: "sm",
				tooltip: __("More"),
				attrs: { "aria-label": __("More actions for {0}", [interview.interview_type]) },
			},
			align: "end",
			options: [
				{
					label: __("Reschedule"),
					icon: "calendar-clock",
					onclick: () =>
						hrms.reschedule_interview({
							interview,
							on_rescheduled: () => this.view.refresh(data.name),
						}),
				},
			],
		});
	}

	/** What the ItemList `controls` slot holds at the right end of the offer row: an answer dropdown while the offer is unanswered, else a plain badge. */
	make_offer_controls(offer, data) {
		const label = get_offer_status_label(offer);
		const theme = OFFER_BADGE_THEMES[offer.status];
		const answers = {
			"Ready to Send": ["Ready to Send", "Awaiting Response", "Accepted", "Rejected"],
			"Awaiting Response": ["Awaiting Response", "Accepted", "Rejected"],
		}[offer.status];
		if (offer.docstatus !== 1 || !answers) {
			return frappe.ui.badge({ label, theme });
		}
		return this.make_status_dropdown({
			label,
			aria_label: __("Offer status: {0}", [label]),
			options: answers.map((status) => ({
				label: get_offer_status_label({ ...offer, status }),
				selected: status === offer.status,
				run: () => this.set_offer_answer(offer, data, status),
			})),
		});
	}

	/**
	 * A plain dropdown button showing the current status. Choosing another one runs its `run()`
	 * (a promise) with the button busy; choosing the current one does nothing, unless the option sets `allow_current`.
	 */
	make_status_dropdown({ label, aria_label, options }) {
		const dropdown = new frappe.ui.Dropdown({
			button: {
				label,
				icon_right: "chevron-down",
				variant: "subtle",
				size: "sm",
				attrs: { "aria-label": aria_label },
			},
			align: "end",
			options: this.make_menu_groups(options, (option) => ({
				label: option.label,
				// the current choice is checked at the right edge; `selected` would draw a left check
				icon_right: option.selected ? "check" : null,
				onclick: () => {
					if (option.selected && !option.allow_current) return;
					dropdown.$trigger.attr("aria-busy", "true");
					option.run().finally(() => dropdown.$trigger.removeAttr("aria-busy"));
				},
			})),
		});
		return dropdown.$trigger;
	}

	/** Menu items, with a divider (a hidden-label group) before each option flagged `divider_before`. */
	make_menu_groups(options, make_item) {
		const groups = [];
		for (const option of options) {
			if (option.divider_before || !groups.length)
				groups.push({ group: "", hide_label: true, options: [] });
			groups.at(-1).options.push(make_item(option));
		}
		return groups;
	}

	// Interview result

	async set_result(interview, data, status) {
		const { previous_status } = await frappe.xcall(`${APPLICANT_API}.set_interview_result`, {
			interview: interview.name,
			status,
		});
		const toast = frappe.ui.toast({
			message: this.get_result_message(interview.interview_type, status),
			action: {
				label: __("Undo"),
				onclick: async () => {
					toast.dismiss();
					await frappe.xcall(`${APPLICANT_API}.set_interview_result`, {
						interview: interview.name,
						status: previous_status,
					});
					this.view.refresh(data.name);
				},
			},
		});
		this.view.refresh(data.name);
	}

	get_result_message(type, status) {
		if (status === "Cleared") return __("{0} marked cleared", [type]);
		if (status === "Rejected") return __("{0} marked rejected", [type]);
		if (status === "Cancelled") return __("{0} cancelled", [type]);
		if (status === "Under Review") return __("{0} moved back to under review", [type]);
		return __("{0} moved back to pending", [type]);
	}

	// Interview result: confirmed, then submitted

	/** Resolves once the dialog is answered, so the dropdown stops looking busy either way. */
	confirm_result(interview, data, status) {
		const is_cleared = status === "Cleared";
		return new Promise((resolve) => {
			const interview_type = escape_html(interview.interview_type);
			const dialog = hrms.hiring.open_confirm_dialog({
				title: is_cleared
					? __("Mark {0} as cleared?", [interview_type])
					: __("Mark {0} as rejected?", [interview_type]),
				body: `<p>${escape_html(
					__(
						"This submits the interview. You can still switch between cleared and rejected later.",
					),
				)}</p>`,
				primary_label: is_cleared ? __("Mark cleared") : __("Mark rejected"),
				theme: is_cleared ? "gray" : "red",
				on_confirm: () => this.submit(interview, data, status),
			});
			dialog.onhide = resolve;
		});
	}

	async submit(interview, data, status) {
		const result = await frappe.xcall(`${APPLICANT_API}.submit_interview`, {
			interview: interview.name,
			status,
		});
		frappe.ui.toast({ message: this.get_result_message(interview.interview_type, status) });
		this.view.refresh(data.name);
		if (result.reject_applicant) this.offer_to_reject(data);
	}

	/** The form asks the same after a rejected interview is submitted. Never done on its own. */
	offer_to_reject(data) {
		hrms.hiring.open_confirm_dialog({
			title: __("Also reject {0}?", [escape_html(data.applicant_name)]),
			body: `<p>${escape_html(__("The interview was marked rejected."))}</p>`,
			primary_label: __("Reject applicant"),
			theme: "red",
			secondary_label: __("Keep"),
			on_confirm: async () => {
				// the dialog closes first, so the reject flow's own dialog doesn't stack on it
				setTimeout(() => this.view.reject({ id: data.name, title: data.applicant_name }));
			},
		});
	}

	// Offer answer

	async set_offer_answer(offer, data, status) {
		const { previous_status, previous_applicant_status, closed_interviews } =
			await frappe.xcall("hrms.hr.doctype.job_offer.job_offer.set_offer_answer", {
				job_offer: offer.name,
				status,
			});
		const toast = frappe.ui.toast({
			message: this.get_offer_message(data, status),
			action: {
				label: __("Undo"),
				onclick: async () => {
					toast.dismiss();
					await frappe.xcall("hrms.hr.doctype.job_offer.job_offer.set_offer_answer", {
						job_offer: offer.name,
						status: previous_status,
						applicant_status: previous_applicant_status,
						closed_interviews,
					});
					this.view.refresh(data.name);
				},
			},
		});
		this.view.refresh(data.name);
	}

	get_offer_message(data, status) {
		if (status === "Accepted")
			return __("Offer marked accepted. {0} moved to Hired.", [data.applicant_name]);
		if (status === "Rejected")
			return __("Offer marked declined. {0} moved to Rejected.", [data.applicant_name]);
		if (status === "Awaiting Response") return __("Offer marked sent");
		return __("Offer moved back to ready to send");
	}
};
