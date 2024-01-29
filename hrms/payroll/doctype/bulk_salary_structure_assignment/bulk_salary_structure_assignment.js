// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bulk Salary Structure Assignment", {
	setup: function (frm) {
		frm.trigger("set_query");
		frappe.model.with_doctype("Employee", () =>
			frm.trigger("setup_filter_group")
		);
	},

	refresh(frm) {
		frm.trigger("get_employees");
	},

	from_date(frm) {
		frm.trigger("get_employees");
	},

	company(frm) {
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

	set_query(frm) {
		frm.set_query("payroll_payable_account", function () {
			return {
				filters: {
					root_type: "Liability",
					is_group: 0,
				},
			};
		});
	},

	setup_filter_group(frm) {
		const filter_wrapper = frm.fields_dict.filter_list.$wrapper;
		filter_wrapper.empty();

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
				frm.events.render_employees_table(frm);
			});
	},

	render_employees_table(frm) {
		const columns = frm.events.get_columns_for_employees_table();

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
		};
		frm.employees_datatable = new frappe.DataTable(
			frm.employee_wrapper.get(0),
			datatable_options
		);
	},

	get_columns_for_employees_table() {
		return [
			{
				name: "employee",
				id: "employee",
				content: __("Employee"),
			},
			{
				name: "employee_name",
				id: "employee_name",
				content: __("Name"),
			},
			{
				name: "company",
				id: "company",
				content: __("Company"),
			},
			{
				name: "department",
				id: "department",
				content: __("Department"),
			},
		].map((x) => ({
			...x,
			editable: false,
			focusable: false,
			dropdown: false,
			align: "left",
		}));
	},
});
