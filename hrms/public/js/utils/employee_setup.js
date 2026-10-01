// First-employees setup: a dialog that keeps returning until the site has a few employees.
frappe.provide("hrms.employee_setup");

const API = "hrms.api.employee_setup";
const LATER_KEY = "hrms_employee_setup_later";
const DEFAULT_TAB = "file";
const EMPTY_ROW = () => ({
	employee_name: "",
	email: "",
	gender: "",
	date_of_birth: "",
});

$(document).on("app_ready", () => {
	const status = frappe.boot.hrms_employee_setup;
	if (!status?.show || !frappe.boot.setup_complete) return;
	// the router closes open dialogs while it renders a page, so wait for that page
	const when_page_ready = () => {
		if (frappe.container?.page) setTimeout(() => hrms.employee_setup.on_route(status), 400);
		else setTimeout(when_page_ready, 200);
	};
	when_page_ready();
	frappe.router.on("change", when_page_ready);
});

hrms.employee_setup = {
	async on_route(status) {
		if (this.done) return;
		const route = frappe.get_route();
		const in_scope = await this.is_hrms_route(route, status);
		if (route.join("/") !== frappe.get_route().join("/")) return;

		this.in_scope = in_scope;
		if (!in_scope) {
			if (this.dialog?.display) this.dialog.hide();
			this.hide_bar();
		} else if (!this.status) {
			this.start(status);
		} else if (!this.dialog?.display) {
			this.show_bar();
		}
	},

	async is_hrms_route(route, status) {
		const [view, name] = route;
		let module;
		if (view === "Workspaces") {
			module = frappe.workspaces[frappe.router.slug(route[route.length - 1] || "")]?.module;
		} else if (["List", "Form", "Tree"].includes(view) && name) {
			await frappe.model.with_doctype(name);
			module = frappe.get_meta(name)?.module;
		} else if (view === "query-report") {
			return (status.reports || []).includes(name);
		} else {
			return (status.pages || []).includes(view);
		}
		return Boolean(module) && frappe.boot.module_app?.[frappe.scrub(module)] === "hrms";
	},

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
						fieldtype: "Date",
						fieldname: "date_of_birth",
						label: __("Date of Birth"),
						in_list_view: 1,
						columns: 2,
					},
				],
			},
			{ fieldtype: "HTML", fieldname: "manual_note" },
			{ fieldtype: "HTML", fieldname: "manual_result" },
			{ fieldtype: "HTML", fieldname: "demo" },
			{ fieldtype: "HTML", fieldname: "demo_result" },
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
				<li class="nav-item"><a class="nav-link" data-tab="demo" href="#">${__("Use demo data")}</a></li>
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
				"A login is created for each email. Date of joining is set to today and can be corrected later on the Employee record.",
			)}</p>`,
		);

		this.dialog.show();
		this.make_paste_area();
		this.render_demo();
		this.activate_tab(tab);
		frappe.require("file_uploader.bundle.js").then(() => this.make_uploader());
	},

	tab_fields: {
		file: ["company", "file_intro", "uploader", "paste", "mapping", "file_result"],
		manual: ["company", "employees", "manual_note", "manual_result"],
		demo: ["company", "demo", "demo_result"],
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
		} else if (name === "demo") {
			this.dialog.set_primary_action(__("Add Demo Employees"), () => this.on_primary());
			this.dialog.get_primary_btn().prop("disabled", false);
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
			.employee-setup-mapping .src .sample { font-family: var(--font-stack); color: var(--text-color); font-size: var(--text-sm); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
			.employee-setup-mapping .arrow { text-align: center; color: var(--text-light); }
			.employee-setup-mapping select { width: 100%; }
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
			upload_notes: __("Excel or CSV"),
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
					"Paste rows copied from Excel, Google Sheets or a CSV, with or without the header row",
				)}</label>
				<textarea class="form-control" rows="4" placeholder="${__(
					"Full Name	Work Email	Gender	Date of Birth	Date of Joining",
				)}"></textarea>
			</div>`);
		const textarea = wrapper.find("textarea");
		const read = frappe.utils.debounce(() => {
			const content = textarea.val();
			if (!content.trim()) {
				if (this.source?.type === "paste") this.on_source_change(null);
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
				<div class="src">${frappe.utils.escape_html(c.header)}${
					!d.has_header && c.sample
						? `<div class="sample">${frappe.utils.escape_html(c.sample)}</div>`
						: ""
				}</div>
				<div class="arrow">→</div>
				<select class="form-control input-xs" data-header="${frappe.utils.escape_html(
					c.header,
				)}" data-index="${i}">${options}</select>`,
			)
			.join("");
		const detect = d.has_header
			? __(
					"Columns matched by their headers. Check them below; anything unmatched is skipped.",
			  )
			: __(
					"No header row, so columns were guessed from the data. Check them below; anything unmatched is skipped.",
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
				<p class="text-muted small">${__(
					"Just exploring? Start with these demo employees and try leave, attendance and payroll with them. They have no logins and can be deleted later.",
				)}</p>
				<table class="table table-sm">
					<thead><tr>
						<th>${__("Name")}</th><th>${__("Designation")}</th><th>${__("Department")}</th>
						<th>${__("Reports To")}</th><th>${__("Joined")}</th>
					</tr></thead>
					<tbody>${body}</tbody>
				</table>
			</div>`);
	},

	async add_demo() {
		this.dialog.get_primary_btn().prop("disabled", true);
		try {
			const result = await frappe.xcall(`${API}.create_demo_employees`, {
				company: this.dialog.get_value("company") || this.status.default_company,
			});
			this.apply_result(result, "demo_result");
		} finally {
			this.dialog.get_primary_btn().prop("disabled", false);
		}
	},

	on_primary() {
		const actions = {
			file: () => this.import_rows(),
			manual: () => this.add_manual(),
			demo: () => this.add_demo(),
		};
		actions[this.active_tab]();
	},

	async add_manual() {
		const today = frappe.datetime.get_today();
		const rows = (this.dialog.get_value("employees") || [])
			.filter((r) => ["employee_name", "email", "gender", "date_of_birth"].some((f) => r[f]))
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
		} finally {
			this.dialog.get_primary_btn().prop("disabled", false);
		}
	},

	skipped_rows(result) {
		return [
			...result.incomplete.map((r) => ({
				...r,
				reason: __("Missing {0}", [r.missing.join(", ")]),
			})),
			...result.errors.map((r) => ({ ...r, reason: r.message })),
		].sort((a, b) => a.row_number - b.row_number);
	},

	notify_skipped(skipped, target, added) {
		const esc = frappe.utils.escape_html;
		const rows = skipped
			.map(
				(r) => `<tr>
					<td class="text-nowrap">${__("Row {0}", [r.row_number])}</td>
					<td>${esc(r.row.employee_name || r.row.first_name || "")}</td>
					<td>${esc(r.reason)}</td>
				</tr>`,
			)
			.join("");
		frappe.msgprint({
			title:
				skipped.length === 1
					? __("1 row was skipped")
					: __("{0} rows were skipped", [skipped.length]),
			indicator: "orange",
			message: `<p>${[
				added ? __("The other rows were added.") : "",
				target === "manual_result" && !this.done
					? __("The skipped rows are still in the table, fix them and add them again.")
					: __("Fix these in your sheet and import them again."),
			].join(" ")}</p>
				<table class="table table-sm small">
					<thead><tr><th>${__("Row")}</th><th>${__("Name")}</th><th>${__("Reason")}</th></tr></thead>
					<tbody>${rows}</tbody>
				</table>`,
			wide: true,
		});
	},

	apply_result(result, target) {
		this.status.active_employees = result.active_employees;
		this.render_progress();

		const skipped = this.skipped_rows(result);
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
		if (skipped.length) {
			parts.push(
				`<span class="text-warning">${
					skipped.length === 1
						? __("1 row skipped")
						: __("{0} rows skipped", [skipped.length])
				}</span>: ${skipped.map((r) => __("Row {0}", [r.row_number])).join(", ")}`,
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
		if (skipped.length) this.notify_skipped(skipped, target, result.created.length);
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
		if (!this.in_scope || this.done || this.status.active_employees >= this.status.required)
			return;
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
