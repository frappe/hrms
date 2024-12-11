// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bulk Salary Structure Assignment", {
	setup(frm) {
		frm.trigger("set_queries");
		hrms.setup_employee_filter_group(frm);
	},

	async refresh(frm) {
		frm.page.clear_indicator();
		frm.disable_save();
		frm.trigger("set_primary_action");
		await frm.trigger("set_payroll_payable_account");
		frm.trigger("get_employees");
		hrms.handle_realtime_bulk_action_notification(
			frm,
			"completed_bulk_salary_structure_assignment",
			"Salary Structure Assignment",
		);
	},

	from_date(frm) {
		frm.trigger("get_employees");
	},

	async company(frm) {
		await frm.trigger("set_payroll_payable_account");
		frm.trigger("get_employees");
	},

	branch(frm) {
		frm.trigger("get_employees");
	},

	department(frm) {
		frm.trigger("get_employees");
	},

	employment_type(frm) {
		frm.trigger("get_employees");
	},

	designation(frm) {
		frm.trigger("get_employees");
	},

	grade(frm) {
		frm.trigger("get_employees");
	},

	set_primary_action(frm) {
		frm.page.set_primary_action(__("Assign Structure"), () => {
			frm.trigger("assign_structure");
		});
	},

	set_queries(frm) {
		frm.set_query("salary_structure", function () {
			return {
				filters: {
					company: frm.doc.company,
					is_active: "Yes",
					docstatus: 1,
				},
			};
		});
		frm.set_query("income_tax_slab", function () {
			return {
				filters: {
					company: frm.doc.company,
					disabled: 0,
					docstatus: 1,
					currency: frm.doc.currency,
				},
			};
		});
		frm.set_query("payroll_payable_account", function () {
			const company_currency = erpnext.get_currency(frm.doc.company);
			return {
				filters: {
					company: frm.doc.company,
					root_type: "Liability",
					is_group: 0,
					account_currency: ["in", [frm.doc.currency, company_currency]],
				},
			};
		});
	},

	set_payroll_payable_account(frm) {
		frappe.db.get_value("Company", frm.doc.company, "default_payroll_payable_account", (r) => {
			frm.set_value("payroll_payable_account", r.default_payroll_payable_account);
		});
	},

	get_employees(frm) {
		if (!frm.doc.from_date) return frm.events.render_employees_datatable(frm, []);

		frm.call({
			method: "get_employees",
			args: {
				advanced_filters: frm.advanced_filters || [],
			},
			doc: frm.doc,
		}).then((r) => frm.events.render_employees_datatable(frm, r.message));
	},

	render_employees_datatable(frm, employees) {
		frm.checked_rows_indexes = [];

		const columns = frm.events.get_employees_datatable_columns();
		const no_data_message = __(
			frm.doc.from_date
				? "There are no employees without a Salary Structure Assignment on this date based on the given filters."
				: "Please select From Date.",
		);
		const get_editor = (colIndex, rowIndex, value, parent, column) => {
			if (!["base", "variable"].includes(column.name)) return;
			const $input = document.createElement("input");
			$input.className = "dt-input h-100";
			$input.type = "number";
			$input.min = 0;
			parent.appendChild($input);
			return {
				initValue(value) {
					$input.focus();
					$input.value = value;
				},
				setValue(value) {
					$input.value = value;
				},
				getValue() {
					return Number($input.value);
				},
			};
		};
		const events = {
			onCheckRow() {
				frm.trigger("handle_row_check");
			},
		};

		hrms.render_employees_datatable(
			frm,
			columns,
			employees,
			no_data_message,
			get_editor,
			events,
		);
	},

	get_employees_datatable_columns() {
		return [
			{
				name: "employee",
				id: "employee",
				content: __("Employee"),
				editable: false,
				focusable: false,
			},
			{
				name: "employee_name",
				id: "employee_name",
				content: __("Name"),
				editable: false,
				focusable: false,
			},
			{
				name: "grade",
				id: "grade",
				content: __("Grade"),
				editable: false,
				focusable: false,
			},
			{
				name: "base",
				id: "base",
				content: __("Base"),
			},
			{
				name: "variable",
				id: "variable",
				content: __("Variable"),
			},
		].map((x) => ({
			...x,
			dropdown: false,
			align: "left",
		}));
	},

	render_update_button(frm) {
		["Base", "Variable"].forEach((d) =>
			frm.add_custom_button(
				__(d),
				function () {
					const dialog = new frappe.ui.Dialog({
						title: __("Set {0} for selected employees", [__(d)]),
						fields: [
							{
								label: __(d),
								fieldname: d,
								fieldtype: "Currency",
							},
						],
						primary_action_label: __("Update"),
						primary_action(values) {
							const col_idx = frm.employees_datatable.datamanager.columns.find(
								(col) => col.content === d,
							).colIndex;
							frm.checked_rows_indexes.forEach((row_idx) => {
								frm.employees_datatable.cellmanager.updateCell(
									col_idx,
									row_idx,
									values[d],
									true,
								);
							});
							dialog.hide();
						},
					});
					dialog.show();
				},
				__("Update"),
			),
		);
		frm.update_button_rendered = true;
	},

	handle_row_check(frm) {
		frm.checked_rows_indexes = frm.employees_datatable.rowmanager.getCheckedRows();
		if (!frm.checked_rows_indexes.length && frm.update_button_rendered) {
			["Base", "Variable"].forEach((d) => frm.remove_custom_button(__(d), __("Update")));
			frm.update_button_rendered = false;
		} else if (frm.checked_rows_indexes.length && !frm.update_button_rendered)
			frm.trigger("render_update_button");
	},

	assign_structure(frm) {
		const rows = frm.employees_datatable.getRows();
		const checked_rows_content = [];
		const employees_with_base_zero = [];

		frm.checked_rows_indexes.forEach((idx) => {
			const row_content = {};
			rows[idx].forEach((cell) => {
				if (["employee", "base", "variable"].includes(cell.column.name))
					row_content[cell.column.name] = cell.content;
			});
			checked_rows_content.push(row_content);
			if (!row_content["base"])
				employees_with_base_zero.push(`<b>${row_content["employee"]}</b>`);
		});

		hrms.validate_mandatory_fields(frm, checked_rows_content);
		if (employees_with_base_zero.length)
			return frm.events.validate_base_zero(
				frm,
				employees_with_base_zero,
				checked_rows_content,
			);

		return frm.events.show_confirm_dialog(frm, checked_rows_content);
	},

	validate_base_zero(frm, employees_with_base_zero, checked_rows_content) {
		frappe.warn(
			__("Are you sure you want to proceed?"),
			__("<b>Base</b> amount has not been set for the following employee(s): {0}", [
				employees_with_base_zero.join(", "),
			]),
			() => {
				frm.events.show_confirm_dialog(frm, checked_rows_content);
			},
			__("Continue"),
		);
	},

	show_confirm_dialog(frm, checked_rows_content) {
		frappe.confirm(
			__("Assign Salary Structure to {0} employee(s)?", [checked_rows_content.length]),
			() => {
				frm.events.bulk_assign_structure(frm, checked_rows_content);
			},
		);
	},

	bulk_assign_structure(frm, employees) {
		frm.call({
			method: "bulk_assign_structure",
			doc: frm.doc,
			args: {
				employees: employees,
			},
			freeze: true,
			freeze_message: __("Assigning Salary Structure"),
		});
	},
});
