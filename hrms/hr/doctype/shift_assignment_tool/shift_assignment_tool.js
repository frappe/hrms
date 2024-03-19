// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shift Assignment Tool", {
	setup(frm) {
		hrms.setup_employee_filter_group(frm);
	},

	async refresh(frm) {
		frm.trigger("set_primary_action");
		frm.trigger("get_employees");
	},

	company(frm) {
		frm.trigger("get_employees");
	},

	start_date(frm) {
		frm.trigger("get_employees");
	},

	end_date(frm) {
		frm.trigger("get_employees");
	},

	branch(frm) {
		frm.trigger("get_employees");
	},

	department(frm) {
		frm.trigger("get_employees");
	},

	designation(frm) {
		frm.trigger("get_employees");
	},

	grade(frm) {
		frm.trigger("get_employees");
	},

	employment_type(frm) {
		frm.trigger("get_employees");
	},

	set_primary_action(frm) {
		frm.disable_save();
		frm.page.set_primary_action(__("Assign Shift"), () => {});
	},

	get_employees(frm) {
		if (!frm.doc.start_date)
			return frm.events.render_employees_datatable(frm, []);

		frm
			.call({
				method: "get_employees",
				args: {
					advanced_filters: frm.advanced_filters || [],
				},
				doc: frm.doc,
			})
			.then((r) => frm.events.render_employees_datatable(frm, r.message));
	},

	render_employees_datatable(frm, employees) {
		// section automatically collapses on applying a single filter
		frm.set_df_property("quick_filters_section", "collapsible", 0);
		frm.set_df_property("advanced_filters_section", "collapsible", 0);

		const columns = frm.events.employees_datatable_columns();
		const no_data_message = __(
			frm.doc.start_date
				? "There are no employees without Shift Assignments for these dates based on the given filters."
				: "Please select the assignment date(s)."
		);

		if (frm.employees_datatable) {
			frm.employees_datatable.rowmanager.checkMap = [];
			frm.employees_datatable.options.noDataMessage = no_data_message;
			frm.employees_datatable.refresh(employees, columns);
			return;
		}

		const $wrapper = frm.get_field("employees_html").$wrapper;
		frm.employee_wrapper = $(`<div class="employee_wrapper">`).appendTo(
			$wrapper
		);
		const datatable_options = {
			columns: columns,
			data: employees,
			checkboxColumn: true,
			checkedRowStatus: false,
			serialNoColumn: false,
			dynamicRowHeight: true,
			inlineFilters: true,
			layout: "fluid",
			cellHeight: 35,
			noDataMessage: no_data_message,
			disableReorderColumn: true,
		};
		frm.employees_datatable = new frappe.DataTable(
			frm.employee_wrapper.get(0),
			datatable_options
		);
	},

	employees_datatable_columns() {
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
		].map((x) => ({
			...x,
			editable: false,
			focusable: false,
			dropdown: false,
			align: "left",
		}));
	},
});
