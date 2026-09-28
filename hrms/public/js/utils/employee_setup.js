// First-employees setup: a dialog that keeps returning until the site has a few employees.
frappe.provide("hrms.employee_setup");

const API = "hrms.api.employee_setup";
const LATER_KEY = "hrms_employee_setup_later";
const DEFAULT_TAB = "file";
const EMPTY_ROW = () => ({
	employee_name: "",
	email: "",
	gender: "",
	age: "",
});

$(document).on("app_ready", () => {
	const status = frappe.boot.hrms_employee_setup;
	if (!status?.show || !frappe.boot.setup_complete) return;
	// the router closes open dialogs while it renders the first page, so wait for that page
	const when_page_ready = () => {
		if (frappe.container?.page) setTimeout(() => hrms.employee_setup.start(status), 400);
		else setTimeout(when_page_ready, 200);
	};
	when_page_ready();
});

hrms.employee_setup = {
	start(status) {
		this.status = status;
		this.ensure_styles();
		let later = false;
		try {
			later = sessionStorage.getItem(LATER_KEY) === status.session;
		} catch (e) {
			later = false;
		}
		later ? this.show_bar() : this.show_dialog();
	},

	remaining() {
		return Math.max(0, this.status.required - this.status.active_employees);
	},

	show_dialog(tab = DEFAULT_TAB) {
		this.hide_bar();
		if (this.dialog) {
			this.dialog.show();
			this.activate_tab(tab);
			return;
		}

		const fields = [{ fieldtype: "HTML", fieldname: "tabs" }];
		if (this.status.companies?.length > 1) {
			fields.push({
				fieldtype: "Link",
				fieldname: "company",
				label: __("Company"),
				options: "Company",
				reqd: 1,
				default: this.status.default_company,
			});
		}
		fields.push(
			{ fieldtype: "HTML", fieldname: "file_intro" },
			{ fieldtype: "HTML", fieldname: "uploader" },
			{ fieldtype: "HTML", fieldname: "paste" },
			{ fieldtype: "HTML", fieldname: "mapping" },
			{ fieldtype: "HTML", fieldname: "file_result" },
			{ fieldtype: "HTML", fieldname: "demo" },
			{
				fieldtype: "Table",
				fieldname: "employees",
				label: __("Employees"),
				in_place_edit: true,
				data: [EMPTY_ROW(), EMPTY_ROW(), EMPTY_ROW()],
				get_data: () => this.dialog?.fields_dict.employees.df.data || [],
				fields: [
					{
						fieldtype: "Data",
						fieldname: "employee_name",
						label: __("Full Name"),
						in_list_view: 1,
						columns: 2,
						reqd: 1,
					},
					{
						fieldtype: "Data",
						fieldname: "email",
						label: __("Work Email"),
						options: "Email",
						in_list_view: 1,
						columns: 2,
					},
					{
						fieldtype: "Link",
						fieldname: "gender",
						label: __("Gender"),
						options: "Gender",
						in_list_view: 1,
						columns: 2,
					},
					{
						fieldtype: "Int",
						fieldname: "age",
						label: __("Approx. Age"),
						in_list_view: 1,
						columns: 1,
					},
				],
			},
			{ fieldtype: "HTML", fieldname: "manual_note" },
			{ fieldtype: "HTML", fieldname: "manual_result" },
		);

		this.dialog = new frappe.ui.Dialog({
			title: __("Add your first employees"),
			size: "large",
			fields,
			primary_action_label: __("Import"),
			primary_action: () => this.on_primary(),
			secondary_action_label: __("Later"),
			secondary_action: () => this.later(),
		});
		this.dialog.$wrapper
			.find(".modal-header .btn-modal-close")
			.on("click", () => this.later());
		this.dialog.$wrapper.on("hidden.bs.modal", () => {
			if (!this.done) this.show_bar();
		});

		this.render_progress();
		this.dialog.fields_dict.tabs.$wrapper.html(`
			<ul class="nav nav-tabs employee-setup-tabs mb-3">
				<li class="nav-item"><a class="nav-link" data-tab="file" href="#">${__("Upload a file")}</a></li>
				<li class="nav-item"><a class="nav-link" data-tab="manual" href="#">${__("Add manually")}</a></li>
			</ul>`);
		this.dialog.fields_dict.tabs.$wrapper.find("[data-tab]").on("click", (e) => {
			e.preventDefault();
			this.activate_tab($(e.currentTarget).data("tab"));
		});
		this.dialog.fields_dict.file_intro.$wrapper.html(`
			<p class="text-muted small">${__(
				"Drop an employee export or any Excel or CSV with a header row. You get to check the column mapping before anything is created.",
			)} <a class="download-template" href="#">${__("Download a blank template")}</a></p>`);
		this.dialog.fields_dict.file_intro.$wrapper.find(".download-template").on("click", (e) => {
			e.preventDefault();
			this.download_template();
		});
		this.dialog.fields_dict.manual_note.$wrapper.html(
			`<p class="text-muted small mt-2">${__(
				"A login is created for each email. Date of birth is set from the approximate age and date of joining to today; both can be corrected later on the Employee record.",
			)}</p>`,
		);

		this.dialog.show();
		this.make_paste_area();
		this.render_demo();
		this.activate_tab(tab);
		frappe.require("file_uploader.bundle.js").then(() => this.make_uploader());
	},

	tab_fields: {
		file: ["company", "file_intro", "uploader", "paste", "mapping", "file_result", "demo"],
		manual: ["company", "employees", "manual_note", "manual_result"],
	},

	activate_tab(name) {
		this.active_tab = name;
		const visible = new Set(this.tab_fields[name]);
		for (const fieldname of new Set(Object.values(this.tab_fields).flat())) {
			if (!this.dialog.fields_dict[fieldname]) continue;
			this.dialog.set_df_property(fieldname, "hidden", visible.has(fieldname) ? 0 : 1);
		}
		this.dialog.fields_dict.tabs.$wrapper
			.find("[data-tab]")
			.removeClass("active")
			.filter(`[data-tab="${name}"]`)
			.addClass("active");
		this.set_primary_for_tab(name);
	},

	set_primary_for_tab(name) {
		if (name === "file") {
			const count = this.detected?.row_count;
			this.dialog.set_primary_action(
				count === 1
					? __("Import 1 Employee")
					: count
					  ? __("Import {0} Employees", [count])
					  : __("Import"),
				() => this.on_primary(),
			);
			this.dialog.get_primary_btn().prop("disabled", !this.detected);
		} else {
			this.dialog.set_primary_action(__("Add Employees"), () => this.on_primary());
			this.dialog.get_primary_btn().prop("disabled", false);
		}
	},

	ensure_styles() {
		frappe.dom.set_style(
			`
			.employee-setup-intro { margin: 0 0 var(--padding-md); font-size: var(--text-sm); color: var(--text-muted); }
			.employee-setup-bar { position: fixed; left: 50%; bottom: 16px; transform: translateX(-50%); z-index: 1020; width: min(520px, calc(100% - 32px)); display: flex; align-items: center; gap: 12px; padding: 10px 14px; border-radius: var(--border-radius-md); background: var(--card-bg); box-shadow: var(--shadow-lg); border: 1px solid var(--border-color); font-size: var(--text-sm); }
			.employee-setup-bar .btn { margin-left: auto; }
			.employee-setup-uploader { min-height: 120px; }
			.employee-setup-uploader .file-uploader { margin: 0; }
			.employee-setup-or { display: flex; align-items: center; gap: 10px; margin: var(--padding-sm) 0; color: var(--text-muted); font-size: var(--text-xs); text-transform: uppercase; letter-spacing: 0.04em; }
			.employee-setup-or::before, .employee-setup-or::after { content: ""; flex: 1; border-top: 1px solid var(--border-color); }
			.employee-setup-paste textarea { font-family: var(--font-stack-mono, monospace); font-size: var(--text-xs); white-space: pre; }
			.employee-setup-source { display: flex; align-items: center; gap: 8px; padding: 8px 10px; border-radius: var(--border-radius-md); background: var(--bg-green, var(--green-50)); color: var(--text-on-green, var(--green-700)); font-size: var(--text-sm); margin: var(--padding-sm) 0; }
			.employee-setup-source a { margin-left: auto; white-space: nowrap; }
			.employee-setup-mapping { display: grid; grid-template-columns: 1fr 18px 1fr; gap: 4px 8px; align-items: center; font-size: var(--text-sm); }
			.employee-setup-mapping .src { font-family: var(--font-stack-mono, monospace); color: var(--text-muted); font-size: var(--text-xs); }
			.employee-setup-mapping .arrow { text-align: center; color: var(--text-light); }
			.employee-setup-mapping select { width: 100%; }
			.employee-setup-demo { margin-top: var(--padding-lg); padding: var(--padding-sm) var(--padding-md); border: 1px dashed var(--border-color); border-radius: var(--border-radius-md); }
			.employee-setup-demo-head { display: flex; align-items: flex-start; gap: 12px; font-size: var(--text-sm); }
			.employee-setup-demo-head .btn { margin-left: auto; white-space: nowrap; }
			.employee-setup-demo table { margin: var(--padding-sm) 0 0; font-size: var(--text-xs); }
			.employee-setup-demo th { color: var(--text-muted); font-weight: normal; border-top: 0; }
			.employee-setup-result ul { padding-left: 18px; margin: 4px 0 0; }
			.employee-setup-next { display: flex; flex-direction: column; gap: 6px; margin-top: var(--padding-md); }
			.employee-setup-next a { display: flex; align-items: center; gap: 8px; padding: 8px 10px; border: 1px solid var(--border-color); border-radius: var(--border-radius-md); color: var(--text-color); }
			.employee-setup-next a .go { margin-left: auto; color: var(--text-muted); }
			`,
			"employee-setup-style",
		);
	},

	render_progress() {
		const { active_employees: done, required } = this.status;
		let intro = this.dialog.$body.find(".employee-setup-intro");
		if (!intro.length) {
			intro = $(`<p class="employee-setup-intro"></p>`).prependTo(this.dialog.$body);
		}
		let text = __(
			"Frappe HR needs at least {0} employees before leave, attendance and payroll make sense.",
			[required],
		);
		if (done) text += " " + __("{0} added so far.", [done]);
		intro.text(text);
	},

	make_uploader() {
		const wrapper = this.dialog.fields_dict.uploader.$wrapper;
		wrapper.empty().off("change drop").addClass("employee-setup-uploader");
		if (!frappe.ui.FileUploader) return;

		this.uploader = new frappe.ui.FileUploader({
			wrapper,
			allow_multiple: false,
			disable_file_browser: true,
			allow_web_link: false,
			allow_take_photo: false,
			allow_toggle_private: false,
			make_attachments_public: false,
			folder: "Home/Attachments",
			restrictions: { allowed_file_types: [".csv", ".xlsx", ".xls"] },
			upload_notes: __("Excel or CSV. Keka and greytHR exports work as they are."),
			on_success: (file) =>
				this.on_source_change({
					type: "file",
					file_url: file.file_url,
					label: file.file_name,
				}),
		});
		// there is no Upload button when the uploader sits inside the dialog
		wrapper.on("change", "input[type=file]", () => this.upload_selected());
		wrapper.on("drop", () => this.upload_selected());
	},

	upload_selected() {
		setTimeout(() => {
			if (this.uploader?.uploader?.files?.length) this.uploader.upload_files();
		}, 0);
	},

	make_paste_area() {
		const wrapper = this.dialog.fields_dict.paste.$wrapper;
		wrapper.html(`
			<div class="employee-setup-paste">
				<div class="employee-setup-or"><span>${__("or")}</span></div>
				<label class="small text-muted">${__(
					"Paste rows copied from Excel, Google Sheets or a CSV, header row included",
				)}</label>
				<textarea class="form-control" rows="4" placeholder="${__(
					"Full Name	Work Email	Gender	Date of Birth	Date of Joining",
				)}"></textarea>
				<div class="small text-muted mt-1 paste-hint"></div>
			</div>`);
		const textarea = wrapper.find("textarea");
		const hint = wrapper.find(".paste-hint");
		const read = frappe.utils.debounce(() => {
			const content = textarea.val();
			hint.text("");
			if (!content.trim()) {
				if (this.source?.type === "paste") this.on_source_change(null);
				return;
			}
			if (content.trim().split("\n").length < 2) {
				hint.text(__("Include the header row and at least one employee."));
				return;
			}
			this.on_source_change({ type: "paste", content, label: __("pasted rows") });
		}, 400);
		textarea.on("input paste", read);
	},

	async on_source_change(source) {
		this.source = source;
		this.detected = null;
		this.dialog.fields_dict.mapping.$wrapper.empty();
		this.dialog.fields_dict.file_result.$wrapper.empty();
		if (!source) return this.set_primary_for_tab("file");

		try {
			this.detected =
				source.type === "file"
					? await frappe.xcall(`${API}.detect_employee_file`, {
							file_url: source.file_url,
					  })
					: await frappe.xcall(`${API}.detect_pasted_employees`, {
							content: source.content,
					  });
		} catch (e) {
			this.source = null;
			return this.set_primary_for_tab("file");
		}
		this.render_mapping();
		this.set_primary_for_tab("file");
	},

	reset_source() {
		this.dialog.fields_dict.paste.$wrapper.find("textarea").val("");
		this.make_uploader();
		this.on_source_change(null);
	},

	render_mapping() {
		const d = this.detected;
		const options = [`<option value="">${__("Skip this column")}</option>`]
			.concat(d.fields.map((f) => `<option value="${f.value}">${f.label}</option>`))
			.join("");
		const rows = d.columns
			.map(
				(c, i) => `
				<div class="src">${frappe.utils.escape_html(c.header)}</div>
				<div class="arrow">→</div>
				<select class="form-control input-xs" data-header="${frappe.utils.escape_html(
					c.header,
				)}" data-index="${i}">${options}</select>`,
			)
			.join("");
		const detect = d.layout
			? __("Looks like a {0} export. Columns mapped automatically, check them below.", [
					`<b>${d.layout}</b>`,
			  ])
			: __(
					"Columns matched by their headers. Check them below; anything unmatched is skipped.",
			  );

		this.dialog.fields_dict.mapping.$wrapper.html(`
			<div class="employee-setup-source">
				<span>✓ ${
					d.row_count === 1
						? __("1 row in {0}", [frappe.utils.escape_html(this.source.label)])
						: __("{0} rows in {1}", [
								d.row_count,
								frappe.utils.escape_html(this.source.label),
						  ])
				}</span>
				<a href="#" class="reset-source">${__("Start over")}</a>
			</div>
			<p class="small text-muted">${detect}</p>
			<div class="employee-setup-mapping">
				<div class="text-muted small">${__("Column in file")}</div><div></div>
				<div class="text-muted small">${__("Employee field")}</div>${rows}
			</div>`);
		this.dialog.fields_dict.mapping.$wrapper.find("select").each((i, el) => {
			$(el).val(d.columns[i].field || "");
		});
		this.dialog.fields_dict.mapping.$wrapper.find(".reset-source").on("click", (e) => {
			e.preventDefault();
			this.reset_source();
		});
	},

	async render_demo() {
		const wrapper = this.dialog.fields_dict.demo.$wrapper;
		const rows = await frappe.xcall(`${API}.get_demo_employees`);
		const esc = frappe.utils.escape_html;
		const body = rows
			.map(
				(r) => `<tr>
					<td>${esc(r.employee_name)}</td>
					<td>${esc(r.designation)}</td>
					<td>${esc(r.department)}</td>
					<td>${esc(r.reports_to || "")}</td>
					<td>${frappe.datetime.str_to_user(r.date_of_joining)}</td>
				</tr>`,
			)
			.join("");

		wrapper.html(`
			<div class="employee-setup-demo">
				<div class="employee-setup-demo-head">
					<div><b>${__("Just exploring?")}</b> <span class="text-muted">${__(
						"Start with these demo employees and try leave, attendance and payroll with them. They have no logins and can be deleted later.",
					)}</span></div>
					<button class="btn btn-default btn-xs add-demo">${__("Add demo employees")}</button>
				</div>
				<table class="table table-sm">
					<thead><tr>
						<th>${__("Name")}</th><th>${__("Designation")}</th><th>${__("Department")}</th>
						<th>${__("Reports To")}</th><th>${__("Joined")}</th>
					</tr></thead>
					<tbody>${body}</tbody>
				</table>
			</div>`);
		wrapper.find(".add-demo").on("click", () => this.add_demo());
	},

	async add_demo() {
		const button = this.dialog.fields_dict.demo.$wrapper.find(".add-demo");
		button.prop("disabled", true);
		try {
			const result = await frappe.xcall(`${API}.create_demo_employees`, {
				company: this.dialog.get_value("company") || this.status.default_company,
			});
			this.apply_result(result, "file_result");
		} finally {
			button.prop("disabled", false);
		}
	},

	on_primary() {
		this.active_tab === "file" ? this.import_rows() : this.add_manual();
	},

	async add_manual() {
		const today = frappe.datetime.get_today();
		const rows = (this.dialog.get_value("employees") || [])
			.filter((r) => ["employee_name", "email", "gender", "age"].some((f) => r[f]))
			.map((r) => ({ ...r, date_of_joining: r.date_of_joining || today }));
		if (!rows.length) {
			frappe.show_alert({
				message: __("Type at least one employee first."),
				indicator: "orange",
			});
			return;
		}

		this.dialog.get_primary_btn().prop("disabled", true);
		try {
			const result = await frappe.xcall(`${API}.create_employees`, {
				rows,
				company: this.dialog.get_value("company") || this.status.default_company,
			});
			this.apply_result(result, "manual_result");
			this.keep_failed_rows(result);
		} finally {
			this.dialog.get_primary_btn().prop("disabled", false);
		}
	},

	keep_failed_rows(result) {
		const failed = [...result.errors, ...result.incomplete].map((r) => r.row);
		const grid = this.dialog.fields_dict.employees;
		grid.df.data = failed.length ? failed : [EMPTY_ROW()];
		grid.grid.refresh();
	},

	async import_rows() {
		if (!this.source) return;
		const column_map = {};
		this.dialog.fields_dict.mapping.$wrapper.find("select").each((i, el) => {
			column_map[$(el).data("header")] = $(el).val();
		});
		const args = {
			column_map,
			company: this.dialog.get_value("company") || this.status.default_company,
		};
		let method = `${API}.import_pasted_employees`;
		if (this.source.type === "file") {
			method = `${API}.import_employees`;
			args.file_url = this.source.file_url;
		} else {
			args.content = this.source.content;
		}

		this.dialog.get_primary_btn().prop("disabled", true);
		try {
			const result = await frappe.xcall(method, args);
			this.apply_result(result, "file_result");
			if (result.incomplete.length || result.errors.length) {
				this.offer_fix_in_grid(result);
			}
		} finally {
			this.dialog.get_primary_btn().prop("disabled", false);
		}
	},

	offer_fix_in_grid(result) {
		const wrapper = this.dialog.fields_dict.file_result.$wrapper;
		$(
			`<p><button class="btn btn-default btn-xs">${__(
				"Fill in the missing details",
			)}</button></p>`,
		)
			.appendTo(wrapper)
			.find("button")
			.on("click", () => {
				const grid = this.dialog.fields_dict.employees;
				grid.df.data = [...result.incomplete, ...result.errors].map((r) => ({
					...EMPTY_ROW(),
					...r.row,
				}));
				grid.grid.refresh();
				this.activate_tab("manual");
			});
	},

	apply_result(result, target) {
		this.status.active_employees = result.active_employees;
		this.render_progress();

		const parts = [];
		if (result.created.length) {
			parts.push(
				`<span class="text-success">${__("{0} added", [
					result.created.length,
				])}</span>: ${result.created
					.map((r) => frappe.utils.escape_html(r.employee_name))
					.join(", ")}`,
			);
		}
		if (result.incomplete.length) {
			parts.push(
				`${__("{0} rows need more details", [
					result.incomplete.length,
				])}<ul>${result.incomplete
					.map(
						(r) =>
							`<li>${frappe.utils.escape_html(
								r.row.employee_name || __("Row {0}", [r.row_number]),
							)}: ${__("missing")} ${r.missing.join(", ")}</li>`,
					)
					.join("")}</ul>`,
			);
		}
		if (result.errors.length) {
			parts.push(
				`${__("{0} rows failed", [result.errors.length])}<ul>${result.errors
					.map(
						(r) =>
							`<li>${frappe.utils.escape_html(
								r.row.employee_name || __("Row {0}", [r.row_number]),
							)}: ${frappe.utils.escape_html(r.message)}</li>`,
					)
					.join("")}</ul>`,
			);
		}
		if (result.unresolved_managers?.length) {
			parts.push(
				__(
					"Could not find a manager named {0}. Set Reports To on those employees later.",
					[
						result.unresolved_managers
							.map((m) => frappe.utils.escape_html(m.reports_to))
							.join(", "),
					],
				),
			);
		}
		this.dialog.fields_dict[target].$wrapper.html(
			`<div class="employee-setup-result small mt-2">${parts
				.map((p) => `<div>${p}</div>`)
				.join("")}</div>`,
		);

		if (this.status.active_employees >= this.status.required) this.show_done();
	},

	async show_done() {
		this.done = true;
		const steps = await frappe.xcall(`${API}.get_next_steps`);
		const list = steps
			.map(
				(s) => `<a href="#" data-route='${JSON.stringify(s.route)}'>
					<span><b>${s.title}</b> <span class="text-muted">· ${
						s.description
					}</span></span><span class="go">→</span></a>`,
			)
			.join("");

		this.dialog.$body.html(`
			<div class="text-center">
				<h4>${__("{0} employees on the site", [this.status.active_employees])}</h4>
				<p class="text-muted">${__(
					"Leave, attendance and payroll can start now. These usually come next:",
				)}</p>
			</div>
			<div class="employee-setup-next">${list}</div>`);
		this.dialog.$body.find("[data-route]").on("click", (e) => {
			e.preventDefault();
			this.dialog.hide();
			frappe.set_route(...JSON.parse($(e.currentTarget).attr("data-route")));
		});
		this.dialog.$wrapper.find(".btn-modal-secondary").hide();
		this.dialog.set_primary_action(__("Done"), () => this.dialog.hide());
		this.hide_bar();
		frappe.boot.hrms_employee_setup.show = 0;
	},

	later() {
		try {
			sessionStorage.setItem(LATER_KEY, this.status.session);
		} catch (e) {
			// storage blocked; the bar still shows for this page
		}
		this.dialog?.hide();
		this.show_bar();
	},

	show_bar() {
		if (this.done || this.status.active_employees >= this.status.required) return;
		this.hide_bar();
		const { active_employees: done, required } = this.status;
		this.bar = $(`<div class="employee-setup-bar">
			<span>${__("Add at least {0} employees to get started. {1} added so far.", [
				required,
				done,
			])}</span>
			<button class="btn btn-default btn-xs">${__("Continue")}</button>
		</div>`).appendTo("body");
		this.bar
			.find("button")
			.on("click", () => this.show_dialog(this.active_tab || DEFAULT_TAB));
	},

	hide_bar() {
		this.bar?.remove();
		this.bar = null;
	},

	download_template() {
		frappe.tools.downloadify(
			[
				[
					"Full Name",
					"Work Email",
					"Gender",
					"Date of Birth",
					"Date of Joining",
					"Department",
					"Designation",
					"Reports To",
				],
				[
					"Priya Nair",
					"priya@example.com",
					"Female",
					"1994-04-12",
					"2026-09-01",
					"Engineering",
					"Engineer",
					"",
				],
			],
			null,
			"employees",
		);
	},
};
