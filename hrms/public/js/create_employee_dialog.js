const JOB_FIELDS = [
	"company",
	"date_of_joining",
	"designation",
	"department",
	"employment_type",
	"grade",
	"branch",
	"reports_to",
];
const PHOTO_FIELD = "image";
const WHOLE_TABS = ["salary_information"];
const WIDE_FIELDTYPES = ["Table", "Text Editor", "Long Text"];

export class CreateEmployeeDialog {
	constructor({ employee, on_created }) {
		this.employee = { ...employee };
		if (!this.employee.salary_mode && this.employee.bank_ac_no)
			this.employee.salary_mode = "Bank";
		this.details = employee.__onload?.employee_details || { fields: [], documents: [] };
		this.on_created = on_created;
	}

	async show() {
		await frappe.model.with_doctype("Employee");
		this.items = this.make_items();
		this.dialog = new frappe.ui.SettingsDialog({ tabs: [{ items: this.items }] });
		this.dialog.$sidebar.prepend(this.make_profile());
		this.build_panels();
		this.dialog.show();
	}

	make_items() {
		const shown = new Set([...JOB_FIELDS, ...this.details.fields].filter(is_reviewable));
		const create = {
			label: __("Create Employee"),
			variant: "solid",
			click: () => this.create(),
		};
		return [
			...get_employee_tabs(shown).map((tab, index) => ({
				id: `tab_${index}`,
				label: tab.label,
				title: tab.label,
				actions: [create],
				fields: get_layout(tab.sections, this.employee),
				fieldnames: tab.sections.flatMap((section) => section.fields),
			})),
			{
				id: "documents",
				label: __("Documents"),
				title: __("Documents"),
				actions: [create],
				render: (panel) => panel.body.append(this.make_documents()),
			},
		];
	}

	build_panels() {
		for (const item of this.items) {
			this.dialog.activate(item.id);
			if (item.fieldnames) {
				this.dialog
					.get_panel(item.id)
					.set_values(pick_values(this.employee, item.fieldnames));
			}
		}
		this.dialog.activate(this.items[0].id);
	}

	make_profile() {
		const { first_name, middle_name, last_name } = this.employee;
		const name = [first_name, middle_name, last_name].filter(Boolean).join(" ");
		const email = this.employee.personal_email || this.employee.company_email || "";
		return $('<div class="epc-profile">').append(
			frappe.ui.avatar({
				image: this.details.photo,
				label: name,
				size: "lg",
				theme: "auto",
			}),
			$('<div class="epc-profile__text">').append(
				$('<div class="text-base font-weight-bold text-ink-gray-8 ellipsis">').text(name),
				$('<div class="text-p-sm text-ink-gray-5 ellipsis">').text(email),
			),
		);
	}

	make_documents() {
		if (!this.details.documents.length) {
			return frappe.ui.empty_state({
				icon: "file",
				title: __("No documents yet"),
				description: __("Documents the new hire uploads appear here."),
			});
		}
		const list = $("<div>");
		for (const document of this.details.documents) {
			list.append(
				$('<a class="epc-document" target="_blank" rel="noopener">')
					.attr("href", document.url)
					.append(frappe.utils.icon("file", "sm"), $("<span>").text(document.label)),
			);
		}
		return list[0];
	}

	async create() {
		const values = {};
		for (const item of this.items.filter((item) => item.fieldnames)) {
			const item_values = this.dialog.get_panel(item.id).get_values();
			if (!item_values) {
				this.dialog.activate(item.id);
				return;
			}
			Object.assign(values, item_values);
		}
		const doc = await frappe.db.insert({ ...without_internal_keys(this.employee), ...values });
		this.dialog.hide();
		this.on_created(doc);
	}
}

function get_employee_tabs(shown) {
	const tabs = [];
	let tab = null;
	let section = null;
	let whole_tab = false;
	for (const df of frappe.get_meta("Employee").fields) {
		if (df.fieldtype === "Tab Break") {
			tab = { label: __(df.label), sections: [] };
			tabs.push(tab);
			section = { label: "", fields: [] };
			whole_tab = WHOLE_TABS.includes(df.fieldname);
		} else if (df.fieldtype === "Section Break") {
			section = { label: df.label ? __(df.label) : "", fields: [] };
		} else if (tab && (shown.has(df.fieldname) || (whole_tab && is_editable(df)))) {
			if (!tab.sections.includes(section)) tab.sections.push(section);
			section.fields.push(df.fieldname);
		}
	}
	return tabs.filter((tab) => tab.sections.length);
}

function get_layout(sections, employee) {
	return sections.flatMap((section, index) => {
		const fields = section.fields.map((fieldname) => get_docfield(fieldname, employee));
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

function get_docfield(fieldname, employee) {
	const df = { ...frappe.meta.get_docfield("Employee", fieldname) };
	if (frappe.model.table_fields.includes(df.fieldtype)) {
		df.fields = frappe.meta.get_docfields(df.options);
		df.data = (employee[fieldname] || []).map((row) => ({ ...row }));
	}
	return df;
}

function is_editable(df) {
	return !df.hidden && !df.read_only && !frappe.model.no_value_type.includes(df.fieldtype);
}

function is_reviewable(fieldname) {
	return fieldname !== PHOTO_FIELD && frappe.meta.has_field("Employee", fieldname);
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
