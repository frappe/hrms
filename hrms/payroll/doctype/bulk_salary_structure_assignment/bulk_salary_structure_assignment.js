// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bulk Salary Structure Assignment", {
	setup(frm) {
		frm.trigger("set_query");
		frm.trigger("setup_filter_group");
	},

	async refresh(frm) {
		frm.trigger("set_primary_action");
		await frm.trigger("set_payroll_payable_account");
		frm.trigger("get_employees");
		frm.trigger("render_update_button");
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
		frm.disable_save();
		frm.page.set_primary_action(__("Assign Structure"), () => {
			frm.trigger("assign_structure");
		});
	},

	set_query(frm) {
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
		frappe.db.get_value(
			"Company",
			frm.doc.company,
			"default_payroll_payable_account",
			(r) => {
				frm.set_value(
					"payroll_payable_account",
					r.default_payroll_payable_account
				);
			}
		);
	},

	render_update_button(frm) {
		["Base", "Variable"].forEach((d) =>
			frm.add_custom_button(
				__(d),
				function () {
					const dialog = new frappe.ui.Dialog({
						title: __("Set {0} for Selected Employees", [__(d)]),
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
								(col) => col.content === d
							).colIndex;
							const checked_rows =
								frm.employees_datatable.rowmanager.getCheckedRows();
							checked_rows.forEach((row_idx) => {
								frm.employees_datatable.cellmanager.updateCell(
									col_idx,
									row_idx,
									values[d],
									true
								);
							});
							dialog.hide();
						},
					});
					dialog.show();
				},
				__("Update")
			)
		);
	},

	setup_filter_group(frm) {
		const filter_wrapper = frm.fields_dict.filter_list.$wrapper;
		filter_wrapper.empty();

		frappe.model.with_doctype("Employee", () => {
			frm.filter_list = new frappe.ui.FilterGroup({
				parent: filter_wrapper,
				doctype: "Employee",
				on_change: () => {
					frm.advanced_filters = frm.filter_list
						.get_filters()
						.reduce((filters, item) => {
							// item[3] is the value from the array [doctype, fieldname, condition, value]
							if (item[3]) {
								filters.push(item.slice(1, 4));
							}
							return filters;
						}, []);
					frm.trigger("get_employees");
				},
			});
		});
	},

	get_employees(frm) {
		frm
			.call({
				method: "get_employees",
				args: {
					advanced_filters: frm.advanced_filters || [],
				},
				doc: frm.doc,
			})
			.then((r) => {
				// section automatically collapses on applying a single filter
				frm.set_df_property("quick_filters_section", "collapsible", 0);
				frm.set_df_property("advanced_filters_section", "collapsible", 0);

				frm.employees = r.message;
				frm.events.render_employees_datatable(frm);
			});
	},

	render_employees_datatable(frm) {
		const columns = frm.events.columns_for_employees_datatable();

		if (frm.employees_datatable) {
			frm.employees_datatable.rowmanager.checkMap = [];
			frm.employees_datatable.refresh(frm.employees, columns);
			return;
		}

		const $wrapper = frm.get_field("employees_html").$wrapper;
		frm.employee_wrapper = $(`<div class="employee_wrapper">`).appendTo(
			$wrapper
		);
		const datatable_options = {
			columns: columns,
			data: frm.employees,
			checkboxColumn: true,
			checkedRowStatus: false,
			serialNoColumn: false,
			dynamicRowHeight: true,
			inlineFilters: true,
			layout: "fluid",
			cellHeight: 35,
			noDataMessage: __("No Data"),
			disableReorderColumn: true,
			getEditor(colIndex, rowIndex, value, parent, column) {
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
						return $input.value;
					},
				};
			},
		};
		frm.employees_datatable = new frappe.DataTable(
			frm.employee_wrapper.get(0),
			datatable_options
		);
	},

	columns_for_employees_datatable() {
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

	assign_structure(frm) {
		const checked_rows = frm.employees_datatable.rowmanager.getCheckedRows();
		const selected_employees = [];
		checked_rows.forEach((idx) =>
			selected_employees.push(frm.employees_datatable.datamanager.data[idx])
		);
		frm
			.call({
				method: "bulk_assign_structure",
				doc: frm.doc,
				args: {
					employees: selected_employees,
				},
				freeze: true,
				freeze_message: __("Assigning Salary Structure"),
			})
			.then((r) => {
				// refresh only on complete/partial success
				if (r.message.success) frm.refresh();
			});
	},
});
