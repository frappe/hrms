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
const NAME_FIELDS = ["first_name", "middle_name", "last_name"];
const EMAIL_FIELDS = ["personal_email", "company_email"];
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
		this.groups = [];
		this.tabs = new frappe.ui.Tabs({ vertical: true, tabs: this.make_tabs() });
		this.tabs.$el.append(this.make_profile());
		this.render_profile();
		this.dialog = new frappe.ui.SettingsDialog({});
		this.dialog.$wrapper.addClass("epc-create-employee");
		this.dialog.$layout.empty().append(this.tabs.el);
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
				content: make_panel_body().append(this.make_documents()),
			},
		];
	}

	make_group(sections) {
		const body = make_panel_body();
		const group = new frappe.ui.FieldGroup({
			body: body[0],
			fields: get_layout(sections, this.employee),
		});
		group.make();
		group.set_values(
			pick_values(
				this.employee,
				sections.flatMap((section) => section.fields),
			),
		);
		this.watch_profile_fields(group);
		this.groups.push(group);
		return body;
	}

	watch_profile_fields(group) {
		for (const fieldname of [...NAME_FIELDS, ...EMAIL_FIELDS]) {
			const field = group.get_field(fieldname);
			if (field) field.df.onchange = () => this.render_profile();
		}
	}

	make_profile() {
		this.$avatar = $(
			'<div class="profile-avatar-upload relative flex shrink-0 rounded-full overflow-hidden cursor-pointer">',
		)
			.attr("title", __("Upload Photo"))
			.on("click", () => this.upload_photo());
		this.$name = $('<div class="text-lg-semibold text-ink-gray-8 ellipsis">');
		this.$email = $('<div class="text-sm text-ink-gray-6 ellipsis">');
		return $('<div class="epc-profile">').append(
			this.$avatar,
			$('<div class="epc-profile__text">').append(this.$name, this.$email),
			frappe.ui.button({
				label: __("Create Employee"),
				variant: "solid",
				onclick: () => this.create(),
			}),
		);
	}

	render_profile() {
		const name = NAME_FIELDS.map((fieldname) => this.get_value(fieldname))
			.filter(Boolean)
			.join(" ");
		const email = EMAIL_FIELDS.map((fieldname) => this.get_value(fieldname)).find(Boolean);
		this.$name.text(name);
		this.$email.text(email || "");
		this.$avatar.empty().append(
			frappe.ui.avatar({
				image: this.employee.image,
				label: name,
				size: "3xl",
				theme: "auto",
			}),
			$(
				'<div class="profile-avatar-overlay absolute inset-0 flex items-center justify-center">',
			).append(frappe.utils.icon("camera", "md")),
		);
	}

	upload_photo() {
		new frappe.ui.FileUploader({
			allow_multiple: false,
			restrictions: { allowed_file_types: ["image/*"] },
			on_success: (file) => {
				this.employee.image = file.file_url;
				this.render_profile();
			},
		});
	}

	get_value(fieldname) {
		const field = this.groups.map((group) => group.get_field(fieldname)).find(Boolean);
		return field ? field.get_value() : this.employee[fieldname];
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

function make_panel_body() {
	return $('<div class="settings-dialog-panel-body">');
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
