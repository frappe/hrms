frappe.provide("frappe.ui.form");

const employee_essentials = () => [
	["first_name", "gender", "designation", "date_of_joining"],
	["last_name", "date_of_birth", "department", "company"],
];

const employee_extras = () => [
	{
		key: "contact",
		label: __("Contact and login"),
		columns: [["personal_email", "create_user_automatically"], ["cell_number"]],
	},
	{
		key: "reporting",
		label: __("Reports to and branch"),
		columns: [["reports_to", "employment_type"], ["branch"]],
	},
	{
		key: "salary",
		label: __("Salary and bank"),
		columns: [
			["ctc", "salary_mode"],
			["salary_currency", "bank_name", "bank_ac_no"],
		],
	},
	{
		key: "approvers",
		label: __("Approvers"),
		columns: [["leave_approver"], ["expense_approver"]],
	},
	{
		key: "emergency",
		label: __("Emergency contact"),
		columns: [["person_to_be_contacted", "relation"], ["emergency_phone_number"]],
	},
];

const EMPLOYEE_FIELD_CONDITIONS = {
	bank_name: (value) => value("salary_mode") === "Bank",
	bank_ac_no: (value) => value("salary_mode") === "Bank",
};

const EMPLOYEE_FIELD_LABELS = {
	create_user_automatically: () => __("Give them a login to the employee portal"),
};

frappe.ui.form.EmployeeQuickEntryForm = class EmployeeQuickEntryForm extends (
	frappe.ui.form.QuickEntryForm
) {
	constructor(...args) {
		super(...args);
		this.extras = employee_extras();
		this.added = new Set();
	}

	set_meta_and_mandatory_fields() {
		this.meta = frappe.get_meta(this.doctype);
		this.docfields = [
			...this.columns_to_fields("essentials", employee_essentials()),
			...this.extras.flatMap((extra) => this.extra_fields(extra)),
			{ fieldtype: "Section Break", fieldname: "add_more_section" },
			{ fieldtype: "HTML", fieldname: "add_more" },
		];
	}

	get_df(fieldname) {
		return frappe.meta.get_docfield(this.doctype, fieldname);
	}

	columns_to_fields(prefix, columns, visible) {
		const fields = [];
		columns.forEach((column, i) => {
			if (i) fields.push({ fieldtype: "Column Break", fieldname: `${prefix}_col_${i}` });
			column
				.filter((fieldname) => this.get_df(fieldname))
				.forEach((fieldname) => fields.push(this.quick_df(fieldname, visible)));
		});
		return fields;
	}

	quick_df(fieldname, visible) {
		const condition = EMPLOYEE_FIELD_CONDITIONS[fieldname];
		const overrides = {
			description: "",
			mandatory_depends_on: "",
			read_only_depends_on: "",
		};
		if (EMPLOYEE_FIELD_LABELS[fieldname]) overrides.label = EMPLOYEE_FIELD_LABELS[fieldname]();
		if (visible || condition) {
			overrides.depends_on = () =>
				(!visible || visible()) &&
				(!condition || condition((f) => this.fields_dict[f]?.get_value()));
		}
		Object.assign(frappe.meta.get_docfield(this.doctype, fieldname, this.doc.name), overrides);
		return { ...this.get_df(fieldname), ...overrides };
	}

	open_doc(set_hooks) {
		delete frappe.meta.docfield_copy[this.doctype]?.[this.doc.name];
		super.open_doc(set_hooks);
	}

	extra_fields(extra) {
		const visible = () => this.added.has(extra.key);
		return [
			{
				fieldtype: "Section Break",
				fieldname: `${extra.key}_section`,
				label: extra.label,
				depends_on: visible,
			},
			...this.columns_to_fields(extra.key, extra.columns, visible),
		];
	}

	extra_fieldnames(extra) {
		return extra.columns.flat().filter((fieldname) => this.get_df(fieldname));
	}

	render_dialog() {
		super.render_dialog();
		this.$wrapper.addClass("employee-quick-entry");
		$('<div class="employee-quick-entry-intro">')
			.text(__("Just the basics to create the record. Add the rest now or later."))
			.prependTo(this.$wrapper.find(".modal-body"));
		if (!this.get_value("date_of_joining")) {
			this.set_value("date_of_joining", frappe.datetime.get_today());
		}
		this.extras.forEach((extra) => this.render_extra_head(extra));
		this.render_add_more();
	}

	register_primary_action() {
		super.register_primary_action();
		frappe.ui.button.dress(this.get_primary_btn(), {
			label: __("Create Employee"),
			variant: "solid",
		});
	}

	render_extra_head(extra) {
		const section = this.sections.find((s) => s.df.fieldname === `${extra.key}_section`);
		const $head = section?.wrapper.find(".section-head");
		if (!$head?.length) return;
		$head.addClass("employee-quick-entry-head").append(
			frappe.ui.button({
				label: __("Remove"),
				variant: "ghost",
				size: "sm",
				onclick: () => this.remove_extra(extra),
			}),
		);
	}

	render_add_more() {
		const remaining = this.extras.filter((extra) => !this.added.has(extra.key));
		const $wrapper = this.fields_dict.add_more.$wrapper.empty();
		if (!remaining.length) return;
		$('<div class="employee-quick-entry-more-label">')
			.text(__("Add more now"))
			.appendTo($wrapper);
		const $chips = $('<div class="employee-quick-entry-chips">').appendTo($wrapper);
		remaining.forEach((extra) =>
			$chips.append(
				frappe.ui.button({
					label: extra.label,
					icon: "plus",
					variant: "outline",
					size: "sm",
					onclick: () => this.add_extra(extra),
				}),
			),
		);
	}

	add_extra(extra) {
		this.added.add(extra.key);
		this.refresh_dependency();
		this.render_add_more();
		const first = this.fields_dict[this.extra_fieldnames(extra)[0]];
		setTimeout(() => first?.$input?.trigger("focus"), 50);
	}

	remove_extra(extra) {
		this.added.delete(extra.key);
		this.extra_fieldnames(extra).forEach((fieldname) => {
			this.set_value(fieldname, this.get_df(fieldname).default ?? null);
		});
		this.refresh_dependency();
		this.render_add_more();
	}
};
