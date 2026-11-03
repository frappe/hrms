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
const WIDE_FIELDTYPES = ["Table", "Text Editor", "Long Text"];

export class CreateEmployeeDialog {
	constructor({ employee, on_created }) {
		this.employee = employee;
		this.details = employee.__onload?.employee_details || { fields: [], documents: [] };
		this.on_created = on_created;
		this.groups = [];
	}

	async show() {
		await frappe.model.with_doctype("Employee");
		this.dialog = new frappe.ui.Dialog({
			title: __("Create Employee"),
			size: "extra-large",
			fields: [{ fieldtype: "HTML", fieldname: "body" }],
			primary_action_label: __("Create Employee"),
			primary_action: () => this.create(),
		});
		this.tabs = new frappe.ui.Tabs({ vertical: true, tabs: this.make_tabs() });
		this.dialog.$wrapper.addClass("epc-create-employee");
		this.tabs.el.prepend(this.make_profile()[0]);
		this.dialog.fields_dict.body.$wrapper.empty().append(this.tabs.el);
		this.dialog.show();
	}

	make_tabs() {
		const shown = new Set([...JOB_FIELDS, ...this.details.fields].filter(is_reviewable));
		return [
			...get_employee_tabs(shown).map((tab) => ({
				label: tab.label,
				content: this.make_group(tab.sections),
			})),
			{
				label: __("Documents"),
				icon: "paperclip",
				content: this.make_documents(),
			},
		];
	}

	make_profile() {
		const { first_name, middle_name, last_name } = this.employee;
		const name = [first_name, middle_name, last_name].filter(Boolean).join(" ");
		const email = this.employee.personal_email || this.employee.company_email || "";
		const profile = $('<div class="epc-profile">');
		profile.append(
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
		return profile;
	}

	make_group(sections) {
		const body = document.createElement("div");
		const group = new frappe.ui.FieldGroup({
			body,
			fields: get_layout(sections, this.employee),
		});
		group.make();
		group.set_values(
			pick_values(
				this.employee,
				sections.flatMap((section) => section.fields),
			),
		);
		this.groups.push(group);
		return body;
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
		for (const [index, group] of this.groups.entries()) {
			const group_values = group.get_values();
			if (!group_values) {
				this.tabs.set_active(index);
				return;
			}
			Object.assign(values, group_values);
		}
		const doc = await frappe.db.insert({ ...without_internal_keys(this.employee), ...values });
		this.dialog.hide();
		this.on_created(doc);
	}
}

function is_reviewable(fieldname) {
	return fieldname !== PHOTO_FIELD && frappe.meta.has_field("Employee", fieldname);
}

function get_employee_tabs(shown) {
	const tabs = [];
	let tab = null;
	let section = null;
	for (const df of frappe.get_meta("Employee").fields) {
		if (df.fieldtype === "Tab Break") {
			tab = { label: __(df.label), sections: [] };
			tabs.push(tab);
			section = { label: "", fields: [] };
		} else if (df.fieldtype === "Section Break") {
			section = { label: df.label ? __(df.label) : "", fields: [] };
		} else if (tab && shown.has(df.fieldname)) {
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
