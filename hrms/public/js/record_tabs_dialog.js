const WIDE_FIELDTYPES = ["Table", "Text Editor", "Long Text"];

export class RecordTabsDialog {
	constructor(doctype, doc) {
		this.doctype = doctype;
		this.doc = { ...doc };
		this.groups = [];
	}

	async show() {
		await frappe.model.with_doctype(this.doctype);
		const tabs = this.make_tabs();
		this.tabs = new frappe.ui.Tabs({
			vertical: true,
			tabs,
			on_change: (index, tab) => tab.on_activate?.(),
		});
		this.tabs.$el.append(this.make_profile());
		this.render_profile();
		this.dialog = new frappe.ui.SettingsDialog({});
		this.dialog.$wrapper
			.addClass("eo-record-dialog")
			.toggleClass("eo-record-dialog--single", tabs.length === 1);
		this.dialog.$layout.empty().append(this.tabs.el);
		this.dialog.show();
	}

	make_field_tabs(include, { lead = [] } = {}) {
		return with_lead_fields(get_tabs(this.doctype, include), lead).map((tab) => ({
			label: tab.label,
			content: this.make_group(tab.sections),
		}));
	}

	make_group(sections) {
		const body = make_panel_body();
		const group = new frappe.ui.FieldGroup({
			body: body[0],
			is_dialog: true,
			fields: get_layout(this.doctype, sections, this.doc).map((df) =>
				without_fetch(this.prepare_field(df)),
			),
		});
		group.make();
		group.set_values(
			pick_values(
				this.doc,
				sections.flatMap((section) => [...(section.lead || []), ...section.fields]),
			),
		);
		this.setup_group(group);
		this.groups.push(group);
		body.on("awesomplete-open", "input", (event) => reveal_dropdown(event.target));
		return body;
	}

	prepare_field(df) {
		return df;
	}

	setup_group(group) {}

	watch_fields(group, handlers) {
		for (const [fieldname, handler] of Object.entries(handlers)) {
			const field = group.get_field(fieldname);
			if (field) field.df.onchange = handler;
		}
	}

	make_profile() {
		this.$avatar = this.make_avatar();
		this.$name = $('<div class="text-lg-semibold text-ink-gray-8 ellipsis">');
		this.$email = $('<div class="text-sm text-ink-gray-6 ellipsis">');
		this.$actions = $('<div class="eo-profile__actions">');
		this.render_actions();
		return $('<div class="eo-profile">').append(
			this.$avatar,
			$('<div class="eo-profile__text">').append(this.$name, this.$email),
			this.$actions,
		);
	}

	render_actions() {
		this.$actions.empty().append(this.get_actions().map((action) => frappe.ui.button(action)));
	}

	make_avatar() {
		return $('<div class="flex shrink-0">');
	}

	render_profile() {
		const { name, email, image } = this.get_profile();
		this.$name.text(name || "");
		this.$email.text(email || "");
		this.$avatar
			.empty()
			.append(frappe.ui.avatar({ image, label: name, size: "3xl", theme: "auto" }));
	}

	get_value(fieldname) {
		const field = this.groups.map((group) => group.get_field(fieldname)).find(Boolean);
		return field ? field.get_value() : this.doc[fieldname];
	}

	set_value(fieldname, value) {
		const group = this.groups.find((group) => group.get_field(fieldname));
		return group ? group.set_value(fieldname, value) : Promise.resolve();
	}

	get_doc({ validate = true } = {}) {
		const values = {};
		for (const [index, group] of this.groups.entries()) {
			if (validate) group.primary_action_fulfilled = true;
			const group_values = group.get_values(!validate);
			if (!group_values) {
				this.tabs.set_active(index);
				return null;
			}
			Object.assign(values, get_empty_values(group), group_values);
		}
		return { ...without_internal_keys(this.doc), ...values };
	}

	async persist() {
		const doc = this.get_doc();
		if (!doc) return null;
		const is_new = !!this.doc.__islocal;
		if (is_new) delete doc.name;
		const saved = await call_quietly(is_new ? "frappe.client.insert" : "frappe.client.save", {
			doc,
		});
		if (saved) this.doc = saved;
		return saved;
	}
}

export function insert_quietly(doc) {
	return call_quietly("frappe.client.insert", { doc });
}

export function call_quietly(method, args) {
	return new Promise((resolve) => {
		frappe.call({
			method,
			args,
			silent: true,
			callback: (r) => resolve(r.message),
			error: (r) => {
				frappe.ui.toast({ type: "error", message: get_error_text(r) });
				resolve(null);
			},
		});
	});
}

function get_error_text(r) {
	const messages = JSON.parse(r?._server_messages || "[]").map((message) =>
		frappe.utils.html2text(JSON.parse(message).message).trim(),
	);
	return messages.join(" ") || __("Could not save the document");
}

export function is_editable(df) {
	const holds_value =
		frappe.model.table_fields.includes(df.fieldtype) ||
		!frappe.model.no_value_type.includes(df.fieldtype);
	return !df.hidden && !df.read_only && holds_value;
}

function reveal_dropdown(input) {
	const list = input.closest(".awesomplete")?.querySelector("ul");
	const panel = input.closest(".settings-dialog-panel-body");
	if (!list || !panel) return;
	const observer = new ResizeObserver(() => {
		if (list.hidden) return;
		const overflow =
			list.getBoundingClientRect().bottom - panel.getBoundingClientRect().bottom;
		if (overflow > 0) panel.scrollTop += overflow;
	});
	observer.observe(list);
	input.addEventListener("awesomplete-close", () => observer.disconnect(), { once: true });
}

export function make_panel_body() {
	return $('<div class="settings-dialog-panel-body">');
}

function get_tabs(doctype, include) {
	let tab = { fieldname: "details", label: __("Details"), sections: [] };
	const tabs = [tab];
	let section = { label: "", fields: [] };
	for (const df of frappe.get_meta(doctype).fields) {
		if (df.fieldtype === "Tab Break") {
			tab = { fieldname: df.fieldname, label: __(df.label), sections: [] };
			tabs.push(tab);
			section = { label: "", fields: [] };
		} else if (df.fieldtype === "Section Break") {
			section = { label: df.label ? __(df.label) : "", fields: [] };
		} else if (include(df, tab.fieldname)) {
			if (!tab.sections.includes(section)) tab.sections.push(section);
			section.fields.push(df.fieldname);
		}
	}
	return tabs.filter((tab) => tab.sections.length);
}

function with_lead_fields(tabs, lead) {
	const fields = tabs.flatMap((tab) => tab.sections.flatMap((section) => section.fields));
	const present = lead.filter((fieldname) => fields.includes(fieldname));
	if (!present.length) return tabs;
	for (const tab of tabs) {
		for (const section of tab.sections) {
			section.fields = section.fields.filter((fieldname) => !present.includes(fieldname));
		}
	}
	const first = tabs[0].sections[0];
	first.lead = present;
	return tabs.map((tab) => ({
		...tab,
		sections: tab.sections.filter((section) => section === first || section.fields.length),
	}));
}

function get_layout(doctype, sections, doc) {
	return sections.flatMap((section, index) => {
		const fields = without_repeated_table_label(
			section,
			section.fields.map((fieldname) => get_docfield(doctype, fieldname, doc)),
		);
		const lead = (section.lead || []).map((fieldname) =>
			get_docfield(doctype, fieldname, doc),
		);
		const wide = fields.filter((df) => WIDE_FIELDTYPES.includes(df.fieldtype));
		const narrow = fields.filter((df) => !wide.includes(df));
		const [left, right] = lead.length
			? split_by_row([...lead, ...narrow])
			: split_in_half(narrow);
		return [
			{ fieldtype: "Section Break", fieldname: `section_${index}`, label: section.label },
			...left,
			...(right.length ? [{ fieldtype: "Column Break", fieldname: `column_${index}` }] : []),
			...right,
			...((left.length || right.length) && wide.length
				? [{ fieldtype: "Section Break", fieldname: `wide_${index}` }]
				: []),
			...wide,
		];
	});
}

function split_by_row(fields) {
	return [fields.filter((df, i) => i % 2 === 0), fields.filter((df, i) => i % 2 === 1)];
}

function split_in_half(fields) {
	const half = Math.ceil(fields.length / 2);
	return [fields.slice(0, half), fields.slice(half)];
}

function without_repeated_table_label(section, fields) {
	const tables = fields.filter((df) => frappe.model.table_fields.includes(df.fieldtype));
	if (!section.label || tables.length !== 1) return fields;
	return fields.map((df) => (df === tables[0] ? { ...df, label: "" } : df));
}

function get_docfield(doctype, fieldname, doc) {
	const df = { ...frappe.meta.get_docfield(doctype, fieldname) };
	if (frappe.model.table_fields.includes(df.fieldtype)) {
		df.fields = frappe.meta.get_docfields(df.options);
		df.data = (doc[fieldname] || []).map((row) => ({ ...row }));
	}
	return df;
}

function without_fetch(df) {
	const { fetch_from, fetch_if_empty, ...rest } = df;
	return rest;
}

function get_empty_values(group) {
	return Object.fromEntries(
		group.fields_list
			.filter((field) => !frappe.model.no_value_type.includes(field.df.fieldtype))
			.map((field) => [field.df.fieldname, null]),
	);
}

function pick_values(doc, fieldnames) {
	return Object.fromEntries(
		fieldnames
			.filter((fieldname) => doc[fieldname] != null)
			.map((fieldname) => [fieldname, doc[fieldname]]),
	);
}

function without_internal_keys(doc) {
	return Object.fromEntries(Object.entries(doc).filter(([key]) => !key.startsWith("__")));
}
