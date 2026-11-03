frappe.provide("frappe.ui.form");

const employee_essentials = () => [
	["first_name", "gender", "designation", "date_of_joining"],
	["last_name", "date_of_birth", "department", "company"],
];

const employee_sections = () => [
	{
		title: __("Contact and login"),
		columns: [["personal_email", "create_user_automatically"], ["cell_number"]],
	},
	{
		title: __("Reports to and branch"),
		columns: [["reports_to", "employment_type"], ["branch"]],
	},
	{
		title: __("Salary and bank"),
		columns: [
			["ctc", "salary_mode"],
			["salary_currency", "bank_name", "bank_ac_no"],
		],
	},
	{
		title: __("Approvers"),
		columns: [["leave_approver"], ["expense_approver"]],
	},
	{
		title: __("Emergency contact"),
		columns: [["person_to_be_contacted", "relation"], ["emergency_phone_number"]],
	},
];

const EMPLOYEE_FIELD_OVERRIDES = {
	create_user_automatically: () => ({
		label: __("Give them a login to the employee portal"),
		description: "",
		depends_on: "",
	}),
};

frappe.ui.form.EmployeeQuickEntryForm = class EmployeeQuickEntryForm extends (
	frappe.ui.form.QuickEntryForm
) {
	async setup() {
		await frappe.require(["optional_sections.bundle.js", "optional_sections.bundle.css"]);
		return super.setup();
	}

	set_meta_and_mandatory_fields() {
		this.meta = frappe.get_meta(this.doctype);
		const essentials = employee_essentials();
		essentials[0].push(...this.missing_mandatory_fields(essentials));
		const shown = new Set(essentials.flat());

		this.detail_sections = employee_sections()
			.map((section) => ({
				...section,
				columns: section.columns.map((column) =>
					column.filter((fieldname) => !shown.has(fieldname) && this.get_df(fieldname)),
				),
			}))
			.filter((section) => section.columns.flat().length);
		this.detail_fields = [];

		this.docfields = [
			{ fieldtype: "HTML", fieldname: "intro" },
			{ fieldtype: "Section Break", fieldname: "essentials_section", hide_border: 1 },
			...this.columns_to_fields("essentials", essentials, (df) => df),
			{ fieldtype: "Section Break", fieldname: "more_details_section", hide_border: 1 },
			{ fieldtype: "HTML", fieldname: "more_details" },
		];
	}

	missing_mandatory_fields(essentials) {
		const shown = new Set(essentials.flat());
		return this.meta.fields
			.filter(
				(df) =>
					df.reqd &&
					!df.hidden &&
					!df.read_only &&
					!frappe.model.no_value_type.includes(df.fieldtype) &&
					!this.doc[df.fieldname] &&
					!shown.has(df.fieldname),
			)
			.map((df) => df.fieldname);
	}

	get_df(fieldname) {
		return frappe.meta.get_docfield(this.doctype, fieldname);
	}

	columns_to_fields(prefix, columns, make_df) {
		return columns.flatMap((column, i) => [
			...(i ? [{ fieldtype: "Column Break", fieldname: `${prefix}_column_${i}` }] : []),
			...column
				.map((fieldname) => this.get_df(fieldname))
				.filter(Boolean)
				.map(make_df),
		]);
	}

	render_dialog() {
		super.render_dialog();
		$('<div class="text-p-sm text-ink-gray-5">')
			.text(__("Just the basics to create the record. Add the rest now or later."))
			.appendTo(this.fields_dict.intro.$wrapper.empty());
		if (!this.get_value("date_of_joining")) {
			this.set_value("date_of_joining", frappe.datetime.get_today());
		}
		this.optional_sections = new frappe.ui.OptionalSections({
			label: __("Add more now"),
			sections: this.detail_sections.map((section, i) => ({
				title: section.title,
				content: () => this.make_detail_section(section, i),
			})),
			on_remove: (i) => this.clear_detail_section(i),
		});
		this.fields_dict.more_details.$wrapper.empty().append(this.optional_sections.$el);
	}

	make_detail_section(section, i) {
		const body = document.createElement("div");
		const fields = new frappe.ui.FieldGroup({
			body,
			fields: this.columns_to_fields(`section_${i}`, section.columns, (df) => ({
				...df,
				...EMPLOYEE_FIELD_OVERRIDES[df.fieldname]?.(),
			})),
		});
		fields.make();
		this.detail_fields[i] = fields;
		return body;
	}

	clear_detail_section(i) {
		const fields = this.detail_fields[i];
		fields?.set_values(
			Object.fromEntries(
				Object.values(fields.fields_dict)
					.filter((f) => f.get_value)
					.map((f) => [f.df.fieldname, f.df.default ?? ""]),
			),
		);
	}

	get_values(ignore_errors, check_invalid) {
		const values = super.get_values(ignore_errors, check_invalid);
		if (!values) return values;
		for (const [i, fields] of this.detail_fields.entries()) {
			if (!fields || !this.optional_sections.is_added(i)) continue;
			const section_values = fields.get_values(ignore_errors, check_invalid);
			if (!section_values) return null;
			Object.assign(values, section_values);
		}
		return values;
	}

	register_primary_action() {
		super.register_primary_action();
		frappe.ui.button.dress(this.get_primary_btn(), {
			label: __("Create Employee"),
			variant: "solid",
		});
	}
};
