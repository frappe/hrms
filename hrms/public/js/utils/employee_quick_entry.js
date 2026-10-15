frappe.provide("frappe.ui.form");

const employee_steps = () => [
	{
		label: __("Personal"),
		columns: [
			["first_name", "last_name"],
			["gender", "date_of_birth"],
		],
	},
	{
		label: __("Job"),
		columns: [
			["company", "date_of_joining", "employment_type"],
			["department", "designation", "reports_to", "branch"],
		],
	},
	{
		label: __("Contact"),
		description: __("Add a personal email to give them a login to the employee portal."),
		columns: [
			["personal_email", "cell_number", "company_email"],
			["user_id", "create_user_automatically"],
		],
	},
	{
		label: __("Payroll"),
		description: __("You can fill these in later from the Salary tab."),
		columns: [
			["ctc", "salary_currency", "salary_mode"],
			["bank_name", "bank_ac_no"],
		],
	},
];

const HIDE_DESCRIPTION = ["user_id", "company_email"];

const EMPLOYEE_FIELD_CONDITIONS = {
	create_user_automatically: (value) => !value("user_id"),
	bank_name: (value) => value("salary_mode") === "Bank",
	bank_ac_no: (value) => value("salary_mode") === "Bank",
};

frappe.ui.form.EmployeeQuickEntryForm = class EmployeeQuickEntryForm extends (
	frappe.ui.form.QuickEntryForm
) {
	constructor(...args) {
		super(...args);
		this.step = 0;
		this.steps = employee_steps();
	}

	set_meta_and_mandatory_fields() {
		this.meta = frappe.get_meta(this.doctype);
		this.step_fields = this.steps.map((step) =>
			step.columns.flat().filter((fieldname) => this.get_df(fieldname)),
		);
		this.docfields = this.steps.flatMap((step, index) => this.step_docfields(step, index));
	}

	get_df(fieldname) {
		return frappe.meta.get_docfield(this.doctype, fieldname);
	}

	step_docfields(step, index) {
		const visible = () => this.step === index;
		const fields = [
			{
				fieldtype: "Section Break",
				fieldname: `step_${index}`,
				description: step.description,
				depends_on: visible,
			},
		];
		step.columns.forEach((column, i) => {
			if (i) fields.push({ fieldtype: "Column Break", fieldname: `step_${index}_col_${i}` });
			column
				.filter((fieldname) => this.get_df(fieldname))
				.forEach((fieldname) => {
					const df = { ...this.get_df(fieldname) };
					const condition = EMPLOYEE_FIELD_CONDITIONS[fieldname];
					df.depends_on = () =>
						visible() &&
						(!condition || condition((f) => this.fields_dict[f]?.get_value()));
					delete df.mandatory_depends_on;
					delete df.read_only_depends_on;
					delete df.collapsible_depends_on;
					if (HIDE_DESCRIPTION.includes(fieldname)) delete df.description;
					fields.push(df);
				});
		});
		return fields;
	}

	render_dialog() {
		super.render_dialog();
		this.$wrapper.addClass("employee-quick-entry");
		if (!this.get_value("date_of_joining"))
			this.set_value("date_of_joining", frappe.datetime.get_today());
		this.stepper = new frappe.ui.Stepper({
			steps: this.steps.map((step) => ({ label: step.label })),
			label: __("New employee steps"),
			is_locked: (index) => index > this.step && this.first_missing(index) !== null,
			on_step_click: (index) => this.go_to(index),
		});
		$('<div class="employee-quick-entry-steps">')
			.append(this.stepper.$el)
			.prependTo(this.$wrapper.find(".modal-body"));
		this.go_to(0);
	}

	register_primary_action() {}

	go_to(index) {
		const blocked = index > this.step ? this.first_missing(index) : null;
		if (blocked !== null) {
			if (blocked !== this.step) index = blocked;
			else return this.show_missing(blocked);
		}
		this.step = index;
		this.stepper.set_current(index);
		this.refresh_dependency();
		this.refresh_actions();
		this.focus_step();
	}

	missing_fields(step) {
		return this.step_fields[step].filter((fieldname) => {
			const field = this.fields_dict[fieldname];
			return field?.df.reqd && is_null(field.get_value());
		});
	}

	first_missing(upto) {
		for (let i = 0; i < upto; i++) {
			if (this.missing_fields(i).length) return i;
		}
		return null;
	}

	show_missing(step) {
		const labels = this.missing_fields(step).map((f) => __(this.fields_dict[f].df.label));
		frappe.show_alert({
			message: __("Fill in {0} to continue.", [labels.join(", ")]),
			indicator: "orange",
		});
	}

	refresh_actions() {
		const last = this.step === this.steps.length - 1;
		if (last) {
			super.register_primary_action();
			frappe.ui.button.dress(this.get_primary_btn(), {
				label: __("Create Employee"),
				variant: "solid",
			});
		} else {
			this.set_primary_action(__("Next"), () => {});
			this.get_primary_btn()
				.off("click")
				.on("click", () => this.go_to(this.step + 1));
		}

		if (this.step) {
			this.set_secondary_action_label(__("Back"));
			this.set_secondary_action(() => this.go_to(this.step - 1));
		} else {
			this.get_secondary_btn().addClass("hide");
		}
	}

	focus_step() {
		const first = this.step_fields[this.step]
			.map((fieldname) => this.fields_dict[fieldname])
			.find((field) => field?.$input && !field.df.read_only);
		setTimeout(() => first?.$input.trigger("focus"), 100);
	}

	setup_cmd_enter_for_save() {
		this.wrapper.keydown((e) => {
			if ((e.ctrlKey || e.metaKey) && e.which == 13 && !frappe.request.ajax_count) {
				this.get_primary_btn().trigger("click");
				e.preventDefault();
				return false;
			}
		});
	}
};
