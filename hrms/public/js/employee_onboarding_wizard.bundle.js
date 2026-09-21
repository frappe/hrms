frappe.provide("hrms.ui");

const WIZARD_STEPS = [
	{ id: "Create User", label: __("Create User") },
	{ id: "Upload Documents", label: __("Upload documents") },
	{ id: "Appointment Letter", label: __("Letter") },
	{ id: "Create Employee", label: __("Employee") },
	{ id: "Assign Masters", label: __("Assignments") },
	{ id: "Activities", label: __("Activities") },
];

const STEP_COUNT = WIZARD_STEPS.length;
const LAST_STEP = STEP_COUNT - 1;

// Beyond this many fields a single column is a long scroll, so split it in two.
const COLUMN_THRESHOLD = 5;

const STEP_FIELDS = {
	3: [
		"employee",
		"department",
		"designation",
		"employee_grade",
		"branch",
		"employment_type",
		"reports_to",
		"holiday_list",
		"gender",
		"date_of_birth",
	],
};

// Steps whose panel is split into titled sections instead of one field list.
const STEP_SECTIONS = {
	0: [
		{
			id: "details",
			title: __("Onboarding Details"),
			fields: [
				"job_offer",
				"job_applicant",
				"employee_name",
				"company",
				"date_of_joining",
				"boarding_begins_on",
			],
		},
		{
			id: "user",
			title: __("User Account"),
			fields: ["personal_email", "company_email", "create_user_for", "user"],
		},
	],
	1: [
		{ id: "documents", fields: ["employee_onboarding_template", "documents"] },
		{ id: "submission", title: __("Submitted Details"), fields: [] },
	],
};

const SECTION_EXTRAS = {
	submission: "render_submission_summary",
};

// Child doctypes behind the portal's repeating sections, used to grid them in the edit dialog.
const SUBMISSION_TABLE_DOCTYPES = {
	education: "Employee Education",
	external_work_history: "Employee External Work History",
};

const ALL_STEP_FIELDS = [
	...Object.values(STEP_FIELDS).flat(),
	...Object.values(STEP_SECTIONS)
		.flat()
		.flatMap((section) => section.fields),
];
const REPARENTED_FIELDS = [...ALL_STEP_FIELDS];

// Maps a checklist row to an action from the shared assignment engine
// (hrms/public/js/utils/employee_assignments.js), which the Employee form uses too.
const ASSIGNMENT_ACTION_LABELS = {
	"Holiday List": "Holiday List",
	"Leave Policy": "Leave Policy",
	"Salary Structure": "Salary Structure",
	"Shift Type": "Shift",
	"Shift Schedule": "Shift Schedule",
};

function format_submission_value(field, value) {
	if (value === null || value === undefined || value === "") return "";
	if (field.fieldtype === "Date") return frappe.datetime.str_to_user(value);
	if (field.fieldtype === "Currency") return format_currency(value);
	// Text Editor arrives as markup, and the summary renders as text.
	if (field.fieldtype === "Text Editor") return $("<div></div>").html(value).text().trim();
	return String(value);
}

function summary_rows(fields, values) {
	return fields
		.map((field) => [field.label, format_submission_value(field, values[field.fieldname])])
		.filter(([, value]) => value);
}

function to_dialog_field(field, values) {
	const dialog_field = {
		fieldname: field.fieldname,
		label: field.label,
		fieldtype: field.fieldtype,
		options: field.options,
		reqd: field.reqd || 0,
	};

	if (field.fieldname in values) dialog_field.default = values[field.fieldname];
	return dialog_field;
}

function section_dialog_fields(section, details) {
	const fields = [{ fieldtype: "Section Break", label: section.label }];
	const half = Math.ceil(section.fields.length / 2);

	section.fields.forEach((field, index) => {
		if (index === half && section.fields.length > COLUMN_THRESHOLD) {
			fields.push({ fieldtype: "Column Break" });
		}
		fields.push(to_dialog_field(field, details));
	});
	return fields;
}

function table_dialog_fields(table, details) {
	return [
		{ fieldtype: "Section Break", label: table.label },
		{
			fieldname: table.fieldname,
			fieldtype: "Table",
			options: SUBMISSION_TABLE_DOCTYPES[table.fieldname],
			data: (details[table.fieldname] || []).map((row) => ({ ...row })),
			fields: table.fields.map((field) => ({
				...to_dialog_field(field, {}),
				in_list_view: 1,
			})),
		},
	];
}

function collect_submission(data, values, dialog) {
	const details = {};

	for (const section of data.sections) {
		for (const field of section.fields)
			details[field.fieldname] = values[field.fieldname] ?? null;
	}

	for (const table of data.tables) {
		const rows = dialog.fields_dict[table.fieldname].grid.get_data() || [];
		details[table.fieldname] = rows.map((row) =>
			Object.fromEntries(
				table.fields.map((field) => [field.fieldname, row[field.fieldname] ?? null]),
			),
		);
	}

	return details;
}

function get_step_index(stage) {
	const index = WIZARD_STEPS.findIndex((step) => step.id === stage);
	return index === -1 ? 0 : index;
}

function get_reached_step(frm) {
	return get_step_index(frm.doc.onboarding_stage);
}

function is_submitted(frm) {
	return frm.doc.docstatus === 1;
}

// What stops a step from being finished, or null when it is done. Next and the
// step rail both read this, so neither can skip past unfinished work.
function get_step_blocker(frm, index) {
	switch (index) {
		case 0:
			return frm.doc.user ? null : __("Create the user to continue");
		case 1:
			return frm.doc.documents_requested_on
				? null
				: __("Send the upload invite to continue");
		case 2:
			// Appointment Letter still requires a Job Applicant, so an offer without one
			// can never complete this step and must not be trapped on it.
			if (!frm.doc.job_applicant) return null;
			return frm.doc.appointment_letter
				? null
				: __("Create the appointment letter to continue");
		case 3:
			return frm.doc.employee ? null : __("Create the employee to continue");
		case 4:
			return assignments_done(frm) ? null : __("Assign or skip every master to continue");
		default:
			return null;
	}
}

function first_blocked_step(frm) {
	for (let index = 0; index < STEP_COUNT; index++) {
		if (get_step_blocker(frm, index)) return index;
	}
	return STEP_COUNT - 1;
}

function can_go_to_step(frm, index) {
	return index <= first_blocked_step(frm);
}

function assignments_done(frm) {
	const rows = frm.doc.assignments || [];
	return rows.length > 0 && rows.every((row) => row.status !== "Pending");
}

function activities_done(frm) {
	const rows = frm.doc.activities || [];
	return rows.every((row) => row.completed);
}

function is_step_completed(frm, index) {
	switch (index) {
		case 0:
			return Boolean(frm.doc.user);
		case 1:
			return Boolean(frm.doc.documents_requested_on);
		case 2:
			return Boolean(frm.doc.appointment_letter);
		case 3:
			return Boolean(frm.doc.employee);
		case 4:
			return assignments_done(frm);
		default:
			return frm.doc.boarding_status === "Completed";
	}
}

function get_initial_step(frm) {
	return Math.min(get_reached_step(frm), first_blocked_step(frm));
}

function status_badge(status) {
	return frappe.ui.badge.html({
		label: __(status),
		theme: status === "Assigned" || status === "Completed" ? "green" : "gray",
		size: "sm",
	});
}

hrms.ui.EmployeeOnboardingWizard = class EmployeeOnboardingWizard {
	constructor({ wrapper, frm }) {
		this.wrapper = wrapper;
		this.frm = frm;
		this._docname = frm.doc?.name || null;
		this.current_step = cint(frm.wizard_step ?? get_initial_step(frm));
		this.build();
		this.refresh_from_frm();
	}

	build() {
		this.$root = $(`
			<div class="eow-root flex justify-center w-full">
				<div class="eow-shell flex flex-col w-full min-w-0 gap-5">
					<div class="eow-stepper-wrap shrink-0 w-full"></div>
					<div class="eow-card flex flex-col w-full min-w-0">
						<div class="eow-compact-stepper shrink-0 pt-4"></div>
						<div class="eow-panel flex flex-col flex-1 min-h-0 min-w-0 w-full py-4"></div>
						<div class="eow-footer flex items-center justify-between shrink-0 w-full border-t mt-auto py-4">
							<div class="eow-footer-left"></div>
							<div class="eow-footer-right flex items-center gap-2"></div>
						</div>
					</div>
				</div>
			</div>
		`);

		$(this.wrapper).empty().append(this.$root);

		this.$card = this.$root.find(".eow-card");
		this.$stepper_wrap = this.$root.find(".eow-stepper-wrap");
		this.$compact_stepper = this.$root.find(".eow-compact-stepper");
		this.$panel = this.$root.find(".eow-panel");
		this.$footer_left = this.$root.find(".eow-footer-left");
		this.$footer_right = this.$root.find(".eow-footer-right");

		this._on_resize = () => {
			if (this._resize_raf) cancelAnimationFrame(this._resize_raf);
			this._resize_raf = requestAnimationFrame(() => this.update_card_height());
		};
		window.addEventListener("resize", this._on_resize, { passive: true });
		this.update_card_height();
	}

	unmount() {
		if (this._resize_raf) cancelAnimationFrame(this._resize_raf);
		if (this._on_resize) window.removeEventListener("resize", this._on_resize);
		this.frm.page?.wrapper?.removeClass("eow-hide-primary");
		this.detach_reparented_fields();
		this.$root?.remove();
	}

	update_card_height() {
		if (!this.$card?.length) return;
		const doc_el = document.documentElement;
		const vw = window.innerWidth || doc_el.clientWidth || screen.width || 1024;
		const vh = window.innerHeight || doc_el.clientHeight || screen.height || 768;
		const is_mobile = vw <= 768;
		const height = Math.max(
			is_mobile ? 480 : 620,
			// the 40/60px subtracted here is .eow-root's vertical padding
			Math.min(820, vh - (is_mobile ? 185 : 265)),
		);
		this.$card.css("min-height", `${height}px`);
	}

	// Always detach before emptying a container that holds them: jQuery .empty()
	// destroys their handlers, which silently kills datepickers and link searches.
	// Detach only the region's own fields, or one region rips out another's.
	detach_fields(fieldnames) {
		for (const fieldname of fieldnames) {
			this.frm.fields_dict?.[fieldname]?.$wrapper?.detach();
		}
	}

	detach_reparented_fields() {
		this.detach_fields(REPARENTED_FIELDS);
	}

	refresh_from_frm() {
		const current_docname = this.frm.doc?.name || null;
		if (current_docname !== this._docname) {
			this._docname = current_docname;
			this.frm.wizard_step = null;
		}

		const target = Math.min(
			cint(this.frm.wizard_step ?? get_initial_step(this.frm)),
			first_blocked_step(this.frm),
		);
		this.frm.wizard_step = target;
		this.current_step = Math.max(0, Math.min(target, STEP_COUNT - 1));

		this.render_stepper();
		this.render_panel();
		this.render_footer();
	}

	set_step(index) {
		index = Math.max(0, Math.min(cint(index), STEP_COUNT - 1));
		if (!can_go_to_step(this.frm, index)) {
			this.explain_lock();
			return;
		}
		if (index === this.current_step) return;
		this.current_step = index;
		this.frm.wizard_step = index;
		this.refresh_from_frm();
	}

	stepper_options() {
		return {
			steps: WIZARD_STEPS.map((step) => ({ label: step.label })),
			current: this.current_step,
			label: __("Onboarding steps"),
			is_locked: (index) => !can_go_to_step(this.frm, index),
			is_completed: (index) => is_step_completed(this.frm, index),
			on_step_click: (index) => this.set_step(index),
			on_locked_click: () => this.explain_lock(),
		};
	}

	explain_lock() {
		frappe.ui.toast({
			message: get_step_blocker(this.frm, first_blocked_step(this.frm)),
			type: "warning",
		});
	}

	render_stepper() {
		if (!this.stepper) {
			const opts = this.stepper_options();
			this.stepper = new frappe.ui.Stepper(opts);
			this.compact_stepper = new frappe.ui.Stepper({ ...opts, compact: true });
			this.$stepper_wrap.append(this.stepper.$el);
			this.$compact_stepper.append(this.compact_stepper.$el);
			return;
		}
		this.stepper.refresh();
		this.compact_stepper.refresh();
		this.stepper.set_current(this.current_step);
		this.compact_stepper.set_current(this.current_step);
	}

	reparent_fields($into, fieldnames) {
		for (const fieldname of fieldnames) {
			const field = this.frm.fields_dict?.[fieldname];
			if (!field?.$wrapper?.length) continue;
			field.$wrapper.appendTo($into).show();
		}
	}

	// Past COLUMN_THRESHOLD fields, split them over two columns so the step fits.
	render_fields($into, fieldnames) {
		if (!fieldnames.length) return;

		if (fieldnames.length <= COLUMN_THRESHOLD) {
			this.reparent_fields(
				$('<div class="eow-fields form-column"></div>').appendTo($into),
				fieldnames,
			);
			return;
		}

		const $columns = $('<div class="eow-columns"></div>').appendTo($into);
		const half = Math.ceil(fieldnames.length / 2);
		for (const group of [fieldnames.slice(0, half), fieldnames.slice(half)]) {
			this.reparent_fields(
				$('<div class="eow-fields form-column"></div>').appendTo($columns),
				group,
			);
		}
	}

	render_panel() {
		this.detach_fields(ALL_STEP_FIELDS);
		this.$panel.empty();

		const sections = STEP_SECTIONS[this.current_step];
		if (sections) {
			for (const section of sections) this.render_section(section);
		} else {
			this.render_fields(this.$panel, STEP_FIELDS[this.current_step] || []);
		}

		const extra = {
			2: () => this.render_appointment_letter(),
			4: () => this.render_assignments(),
			5: () => this.render_activities(),
		}[this.current_step];
		extra?.();
	}

	render_section(section) {
		const $section = $('<div class="eow-section"></div>').appendTo(this.$panel);
		if (section.title) {
			$('<div class="eow-section-title"></div>').text(section.title).appendTo($section);
		}
		this.render_fields($section, section.fields);

		const extra = SECTION_EXTRAS[section.id];
		if (extra) this[extra]($section);
	}

	render_submission_summary($into = this.$panel) {
		if (!this.frm.doc.details_submitted_on) {
			$into.append(
				frappe.ui.empty_state({
					icon: "user",
					title: __("Waiting for the employee"),
					description: __("What they fill in on the upload form appears here."),
				}),
			);
			return;
		}

		$('<div class="eow-section-action"></div>')
			.append(
				frappe.ui.button({
					label: __("View Submitted Details"),
					variant: "subtle",
					icon_left: "eye",
					onclick: () => this.show_submission(),
				}),
			)
			.appendTo($into);
	}

	async show_submission() {
		const dialog = new frappe.ui.Dialog({
			title: __("Submitted on {0}", [
				frappe.datetime.str_to_user(this.frm.doc.details_submitted_on),
			]),
			size: "large",
			fields: [{ fieldtype: "HTML", fieldname: "summary" }],
		});

		// Editing is only safe until the Employee exists; after that the Employee
		// record is the source of truth.
		if (!this.frm.doc.employee) {
			dialog.set_primary_action(__("Edit Details"), () => {
				dialog.hide();
				this.edit_submission();
			});
		}

		dialog.show();

		const $summary = dialog.fields_dict.summary.$wrapper;
		$summary.html(`<div class="text-ink-gray-5">${__("Loading...")}</div>`);
		this.load_submission().then((data) => this.fill_submission_summary($summary, data));
	}

	async load_submission() {
		const response = await this.frm.call({
			method: "get_submitted_details",
			doc: this.frm.doc,
		});
		return response.message;
	}

	fill_submission_summary($into, data) {
		$into.empty();
		const details = data.details || {};

		for (const section of data.sections) {
			this.append_summary_group($into, section.label, summary_rows(section.fields, details));
		}

		for (const table of data.tables) {
			(details[table.fieldname] || []).forEach((entry, index) => {
				const title = `${table.label} ${index + 1}`;
				this.append_summary_group($into, title, summary_rows(table.fields, entry));
			});
		}

		if (!$into.children().length) {
			$into.append(
				frappe.ui.empty_state({ icon: "file-text", title: __("Nothing filled in yet") }),
			);
		}
	}

	append_summary_group($into, title, rows) {
		if (!rows.length) return;

		const $group = $('<div class="eow-summary-group"></div>').appendTo($into);
		$('<div class="eow-summary-title"></div>').text(title).appendTo($group);

		const $list = $('<dl class="eow-summary-list"></dl>').appendTo($group);
		for (const [label, value] of rows) {
			$("<dt></dt>").text(label).appendTo($list);
			$("<dd></dd>").text(value).appendTo($list);
		}
	}

	async edit_submission() {
		const data = await this.load_submission();
		const details = data.details || {};
		const fields = [
			...data.sections.flatMap((section) => section_dialog_fields(section, details)),
			...data.tables.flatMap((table) => table_dialog_fields(table, details)),
		];

		const dialog = new frappe.ui.Dialog({
			title: __("Edit Submitted Details"),
			size: "large",
			fields,
			primary_action_label: __("Save"),
			primary_action: async (values) => {
				dialog.hide();
				await this.frm.call({
					method: "update_submitted_details",
					doc: this.frm.doc,
					args: { details: collect_submission(data, values, dialog) },
					freeze: true,
					freeze_message: __("Saving the details"),
				});
				this.frm.refresh();
			},
		});
		dialog.show();
	}

	render_appointment_letter() {
		const frm = this.frm;
		const $wrap = $('<div class="eow-letter flex flex-col gap-4"></div>').appendTo(
			this.$panel,
		);

		if (!frm.doc.appointment_letter) {
			if (!frm.doc.job_applicant) {
				$wrap.append(
					frappe.ui.empty_state({
						icon: "mail",
						title: __("Appointment Letter needs a Job Applicant"),
						description: __(
							"This Job Offer has no Job Applicant, and Appointment Letter still requires one. Skip this step for now.",
						),
					}),
				);
				return;
			}
			$wrap.append(
				frappe.ui.empty_state({
					icon: "mail",
					title: __("No appointment letter yet"),
					description: __("Create the letter, then send it to the new hire."),
					actions: [
						{
							label: __("Create Appointment Letter"),
							variant: "solid",
							css_class: "eow-create-letter",
						},
					],
				}),
			);
			$wrap.find(".eow-create-letter").on("click", () => this.create_appointment_letter());
			return;
		}

		const $head = $('<div class="flex items-center justify-between gap-2"></div>').appendTo(
			$wrap,
		);
		$head.append(
			frappe.ui.button({
				label: frm.doc.appointment_letter,
				variant: "ghost",
				icon_right: "external-link",
				onclick: () =>
					frappe.set_route("Form", "Appointment Letter", frm.doc.appointment_letter),
			}),
			frappe.ui.button({
				label: frm.doc.appointment_letter_sent_on
					? __("Send Again")
					: __("Send Appointment Letter"),
				variant: "solid",
				icon_left: "send",
				onclick: () =>
					frm
						.call({
							method: "send_appointment_letter",
							doc: frm.doc,
							freeze: true,
							freeze_message: __("Sending the letter"),
						})
						.then(() => frm.refresh()),
			}),
		);

		if (frm.doc.appointment_letter_sent_on) {
			$wrap.append(
				frappe.ui.alert({
					title: __("Sent on {0}", [
						frappe.datetime.str_to_user(frm.doc.appointment_letter_sent_on),
					]),
					theme: "green",
					variant: "subtle",
				}),
			);
		}

		const url = `/printview?doctype=${encodeURIComponent(
			"Appointment Letter",
		)}&name=${encodeURIComponent(frm.doc.appointment_letter)}&trigger_print=0`;
		$wrap.append(
			`<iframe class="eow-letter-preview w-full" src="${url}" title="${__(
				"Appointment letter preview",
			)}"></iframe>`,
		);
	}

	create_appointment_letter() {
		const frm = this.frm;
		frappe.new_doc("Appointment Letter", {
			job_applicant: frm.doc.job_applicant,
			applicant_name: frm.doc.employee_name,
			company: frm.doc.company,
			appointment_date: frm.doc.date_of_joining,
			employee_onboarding: frm.doc.name,
		});
	}

	render_assignments() {
		const frm = this.frm;
		const $list = $('<div class="eow-checklist flex flex-col"></div>').appendTo(this.$panel);
		this.flag_company_holiday_list($list);

		for (const row of frm.doc.assignments || []) {
			const $row = $(`
				<div class="eow-checklist-row flex items-center justify-between gap-3 py-3 border-b">
					<div class="flex flex-col min-w-0">
						<span class="eow-checklist-title">${frappe.utils.escape_html(__(row.master))}</span>
						<span class="eow-checklist-meta text-ink-gray-5">${frappe.utils.escape_html(
							row.reference_name || row.offer_value || __("Not set"),
						)}</span>
					</div>
					<div class="eow-checklist-actions flex items-center gap-2 shrink-0">
						${status_badge(row.status)}
					</div>
				</div>
			`).appendTo($list);

			if (row.status !== "Pending") continue;

			$row.find(".eow-checklist-actions").append(
				frappe.ui.button({
					label: __("Assign"),
					variant: "subtle",
					disabled: !frm.doc.employee,
					onclick: () => this.assign_master(row),
				}),
				frappe.ui.button({
					label: __("Skip"),
					variant: "ghost",
					onclick: () => this.save_assignment(row.master, null),
				}),
			);
		}

		if (!frm.doc.employee) {
			this.$panel.append(
				frappe.ui.alert({
					title: __("Create the Employee record before assigning masters"),
					variant: "subtle",
				}),
			);
		}
	}

	// A holiday list assigned to the company already covers the employee, so an
	// employee-specific assignment is optional. Say so rather than letting HR guess.
	flag_company_holiday_list($list) {
		const frm = this.frm;
		const row = (frm.doc.assignments || []).find((row) => row.master === "Holiday List");
		if (!row || row.status !== "Pending" || !row.offer_value) return;

		frm.call({ method: "get_company_holiday_list", doc: frm.doc }).then((r) => {
			if (r.message !== row.offer_value) return;

			const $row = $list.find(".eow-checklist-row").first();
			if (!$row.length) return;

			$row.find(".eow-checklist-meta").after(
				$('<span class="eow-checklist-note text-ink-gray-5"></span>').text(
					__("Already assigned to {0}. Assigning one to the employee is optional.", [
						frm.doc.company,
					]),
				),
			);
		});
	}

	save_assignment(master, reference_name) {
		return this.frm
			.call({
				method: "set_assignment",
				doc: this.frm.doc,
				args: { master, reference_name },
				freeze: true,
			})
			.then(() => this.frm.refresh());
	}

	// Reuses the Employee form's assignment engine, so the dialog keeps its Submit
	// step, its field hints and its queries. The row is ticked by reconciliation
	// against the real assignment document, not by this callback.
	assign_master(row) {
		const frm = this.frm;
		const label = ASSIGNMENT_ACTION_LABELS[row.master];
		const action = hrms.assignments
			.get_assignment_actions()
			.find((candidate) => candidate.label === __(label));

		if (!action) {
			frappe.ui.toast({
				message: __("No assignment is available for {0}", [__(row.master)]),
			});
			return;
		}

		const ctx = {
			employee: frm.doc.employee,
			employee_name: frm.doc.employee_name,
			company: frm.doc.company,
			date_of_joining: frm.doc.date_of_joining,
		};
		hrms.assignments.open_assignment(ctx, {
			...action,
			redirect: false,
			on_created: () => this.sync_assignments(),
		});
	}

	sync_assignments() {
		return this.frm
			.call({ method: "sync_assignments", doc: this.frm.doc })
			.then(() => this.frm.refresh());
	}

	render_activities() {
		const frm = this.frm;
		const rows = frm.doc.activities || [];
		const $list = $('<div class="eow-checklist flex flex-col"></div>').appendTo(this.$panel);

		if (!rows.length) {
			$list.append(
				frappe.ui.empty_state({
					icon: "clipboard-list",
					title: __("No onboarding activities"),
					description: __("Pick a template above, or finish the onboarding as it is."),
				}),
			);
			return;
		}

		for (const row of rows) {
			const $row = $(`
				<div class="eow-checklist-row flex items-center justify-between gap-3 py-3 border-b">
					<div class="flex flex-col min-w-0">
						<span class="eow-checklist-title">${frappe.utils.escape_html(row.activity_name || "")}</span>
						<span class="eow-checklist-meta text-ink-gray-5">${frappe.utils.escape_html(
							row.user || row.role || "",
						)}</span>
					</div>
					<div class="eow-checklist-actions flex items-center gap-2 shrink-0"></div>
				</div>
			`).appendTo($list);

			$row.find(".eow-checklist-actions").append(
				row.completed
					? $(status_badge("Completed"))
					: frappe.ui.button({
							label: __("Mark Done"),
							variant: "subtle",
							onclick: () =>
								frm
									.call({
										method: "set_activity_completed",
										doc: frm.doc,
										args: { idx: row.idx },
										freeze: true,
									})
									.then(() => frm.refresh()),
					  }),
			);
		}
	}

	render_footer() {
		this.$footer_left.empty();
		this.$footer_right.empty();
		// The wizard saves between steps and submits from its own footer, so the
		// toolbar's primary button is never the right place to act.
		this.frm.page?.wrapper?.addClass("eow-hide-primary");

		if (this.current_step > 0) {
			this.$footer_left.append(
				frappe.ui.button({
					label: __("Back"),
					icon_left: "arrow-left",
					onclick: () => this.set_step(this.current_step - 1),
				}),
			);
		}

		for (const $button of this.get_step_actions()) this.$footer_right.append($button);
	}

	get_step_actions() {
		const frm = this.frm;
		const step = this.current_step;
		const actions = [];

		if (step === 0 && !frm.doc.user) {
			actions.push(
				frappe.ui.button({
					label: __("Create User"),
					variant: "solid",
					onclick: () =>
						this.run("create_user", __("Creating the user")).then(() =>
							frappe.show_alert({
								message: __("User {0} is linked", [frm.doc.user]),
								indicator: "green",
							}),
						),
				}),
			);
		}

		if (step === 1) {
			actions.push(
				frappe.ui.button({
					label: frm.doc.documents_requested_on
						? __("Send Again")
						: __("Invite user to upload documents"),
					variant: "subtle",
					icon_left: "send",
					disabled: !(frm.doc.documents || []).length,
					onclick: () =>
						this.run("send_documents_link", __("Sending the request")).then(() =>
							frappe.show_alert({
								message: __("Invite sent to {0}", [
									frm.doc.company_email || frm.doc.personal_email,
								]),
								indicator: "green",
							}),
						),
				}),
			);
		}

		if (step === 3 && !frm.doc.employee) {
			actions.push(
				frappe.ui.button({
					label: __("Create Employee"),
					variant: "solid",
					onclick: () => this.run("create_employee", __("Creating the employee")),
				}),
			);
			return actions;
		}

		if (step === LAST_STEP) {
			if (is_submitted(frm)) return actions;

			actions.push(
				frappe.ui.button({
					label: __("Submit"),
					variant: "solid",
					onclick: () => this.submit_onboarding(),
				}),
			);
			return actions;
		}

		const blocker = this.step_blocker();
		actions.push(
			frappe.ui.button({
				label: __("Next"),
				variant: this.has_pending_primary() ? "subtle" : "solid",
				icon_right: "arrow-right",
				disabled: Boolean(blocker),
				tooltip: blocker || undefined,
				onclick: () => this.go_next(),
			}),
		);
		return actions;
	}

	step_blocker() {
		return get_step_blocker(this.frm, this.current_step);
	}

	// While a step's own primary action is still outstanding, Next must not compete
	// with it. The stepper component has no say in this - it only draws the rail.
	has_pending_primary() {
		const frm = this.frm;
		switch (this.current_step) {
			case 0:
				return !frm.doc.user;
			case 2:
				return Boolean(frm.doc.job_applicant) && !frm.doc.appointment_letter_sent_on;
			default:
				return false;
		}
	}

	async run(method, freeze_message) {
		await this.save_if_dirty();
		await this.frm.call({ method, doc: this.frm.doc, freeze: true, freeze_message });
		this.frm.refresh();
	}

	async save_if_dirty() {
		if (this.frm.is_new() || this.frm.is_dirty()) await this.frm.save();
	}

	async advance_stage(index) {
		if (index <= get_reached_step(this.frm)) return;
		await this.frm.set_value("onboarding_stage", WIZARD_STEPS[index].id);
		await this.frm.save();
	}

	async go_next() {
		const blocker = this.step_blocker();
		if (blocker) {
			frappe.ui.toast({ message: blocker, type: "warning" });
			return;
		}

		const next = this.current_step + 1;
		await this.save_if_dirty();
		await this.advance_stage(next);
		this.set_step(next);
	}

	async submit_onboarding() {
		await this.save_if_dirty();
		await this.frm.savesubmit();
	}
};
