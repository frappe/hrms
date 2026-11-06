const WIDE_FIELDTYPES = ["Table", "Text Editor", "Long Text"];

export class RecordTabsDialog {
	constructor(doctype, doc) {
		this.doctype = doctype;
		this.doc = { ...doc };
		this.groups = [];
	}

	async show() {
		await frappe.model.with_doctype(this.doctype);
		this.tabs = new frappe.ui.Tabs({
			vertical: true,
			tabs: this.make_tabs(),
			on_change: (index, tab) => tab.on_activate?.(),
		});
		this.tabs.$el.append(this.make_profile());
		this.render_profile();
		this.dialog = new frappe.ui.SettingsDialog({});
		this.dialog.$wrapper.addClass("epc-record-dialog");
		this.dialog.$layout.empty().append(this.tabs.el);
		this.dialog.show();
	}

	make_field_tabs(include) {
		return get_tabs(this.doctype, include).map((tab) => ({
			label: tab.label,
			content: this.make_group(tab.sections),
		}));
	}

	make_group(sections) {
		const body = make_panel_body();
		const group = new frappe.ui.FieldGroup({
			body: body[0],
			fields: get_layout(this.doctype, sections, this.doc).map((df) =>
				without_fetch(this.prepare_field(df)),
			),
		});
		group.make();
		group.set_values(
			pick_values(
				this.doc,
				sections.flatMap((section) => section.fields),
			),
		);
		this.setup_group(group);
		this.groups.push(group);
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
		return $('<div class="epc-profile">').append(
			this.$avatar,
			$('<div class="epc-profile__text">').append(this.$name, this.$email),
			$('<div class="epc-profile__actions">').append(
				this.get_actions().map((action) => frappe.ui.button(action)),
			),
		);
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
			const group_values = group.get_values(!validate);
			if (!group_values) {
				this.tabs.set_active(index);
				return null;
			}
			Object.assign(values, get_empty_values(group), group_values);
		}
		return { ...without_internal_keys(this.doc), ...values };
	}
}

export function is_editable(df) {
	return !df.hidden && !df.read_only && !frappe.model.no_value_type.includes(df.fieldtype);
}

export function make_panel_body() {
	return $('<div class="settings-dialog-panel-body">');
}

function get_tabs(doctype, include) {
	const tabs = [];
	let tab = null;
	let section = null;
	for (const df of frappe.get_meta(doctype).fields) {
		if (df.fieldtype === "Tab Break") {
			tab = { fieldname: df.fieldname, label: __(df.label), sections: [] };
			tabs.push(tab);
			section = { label: "", fields: [] };
		} else if (df.fieldtype === "Section Break") {
			section = { label: df.label ? __(df.label) : "", fields: [] };
		} else if (tab && include(df, tab.fieldname)) {
			if (!tab.sections.includes(section)) tab.sections.push(section);
			section.fields.push(df.fieldname);
		}
	}
	return tabs.filter((tab) => tab.sections.length);
}

function get_layout(doctype, sections, doc) {
	return sections.flatMap((section, index) => {
		const fields = section.fields.map((fieldname) => get_docfield(doctype, fieldname, doc));
		const wide = fields.filter((df) => WIDE_FIELDTYPES.includes(df.fieldtype));
		const narrow = fields.filter((df) => !wide.includes(df));
		const half = Math.ceil(narrow.length / 2);
		return [
			{ fieldtype: "Section Break", fieldname: `section_${index}`, label: section.label },
			...narrow.slice(0, half),
			...(narrow.length
				? [{ fieldtype: "Column Break", fieldname: `column_${index}` }]
				: []),
			...narrow.slice(half),
			...(narrow.length && wide.length
				? [{ fieldtype: "Section Break", fieldname: `wide_${index}` }]
				: []),
			...wide,
		];
	});
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
