// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on("Leave Control Panel", {
	setup: function (frm) {
		frm.trigger("set_query");
		frm.trigger("set_leave_details");
		frappe.model.with_doctype("Employee", () => set_field_options(frm));
	},

	refresh: function (frm) {
		frm.disable_save();
		frm.trigger("load_employees");
		frm.trigger("set_primary_action");
	},

	company: function (frm) {
		if (frm.doc.company) {
			frm.set_query("department", function () {
				return {
					filters: {
						company: frm.doc.company,
					},
				};
			});
		}
		frm.trigger("load_employees");
	},

	employment_type(frm) {
		frm.trigger("load_employees");
	},

	branch(frm) {
		frm.trigger("load_employees");
	},

	department(frm) {
		frm.trigger("load_employees");
	},

	designation(frm) {
		frm.trigger("load_employees");
	},

	employee_grade(frm) {
		frm.trigger("load_employees");
	},

	dates_based_on(frm) {
		frm.trigger("reset_leave_details");
		frm.trigger("load_employees");
	},

	from_date(frm) {
		frm.trigger("load_employees");
	},

	to_date(frm) {
		frm.trigger("load_employees");
	},

	leave_period(frm) {
		frm.trigger("load_employees");
	},

	allocate_based_on_leave_policy(frm) {
		frm.trigger("load_employees");
	},

	leave_type(frm) {
		frm.trigger("load_employees");
	},

	leave_policy(frm) {
		frm.trigger("load_employees");
	},

	reset_leave_details(frm) {
		if (frm.doc.dates_based_on === "Leave Period") {
			frm.add_fetch("leave_period", "from_date", "from_date");
			frm.add_fetch("leave_period", "to_date", "to_date");
		}
	},

	set_leave_details(frm) {
		frm.call("get_latest_leave_period").then((r) => {
			frm.set_value({
				dates_based_on: "Leave Period",
				from_date: frappe.datetime.get_today(),
				to_date: null,
				leave_period: r.message,
				carry_forward: 1,
				allocate_based_on_leave_policy: 1,
				leave_type: null,
				no_of_days: 0,
				leave_policy: null,
				company: frappe.defaults.get_default("company"),
			});
		});
	},

	load_employees(frm) {
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
				frm.set_df_property("filters_section", "collapsible", 0);
				frm.set_df_property("advanced_filters_section", "collapsible", 0);

				frm.employees = r.message;
				frm.set_df_property("select_employees_section", "hidden", 0);
				frm.events.show_employees(frm, frm.employees);
			});
	},

	show_employees(frm, employees) {
		const $wrapper = frm.get_field("employees_html").$wrapper;
		frm.employee_wrapper = $(`<div class="employee_wrapper pb-5">`).appendTo(
			$wrapper
		);
		frm.events.render_datatable(frm, employees, frm.employee_wrapper);
	},

	render_datatable(frm, data, wrapper) {
		const columns = frm.events.get_columns_for_employees_table();
		if (!frm.employees_datatable) {
			const datatable_options = {
				columns: columns,
				data: data,
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
				wrapper.get(0),
				datatable_options
			);
		} else {
			frm.employees_datatable.rowmanager.checkMap = [];
			frm.employees_datatable.refresh(data, columns);
		}
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

	set_query(frm) {
		frm.set_query("leave_policy", function () {
			return {
				filters: {
					docstatus: 1,
				},
			};
		});
		frm.set_query("leave_period", function () {
			return {
				filters: {
					is_active: 1,
				},
			};
		});
	},

	set_primary_action(frm) {
		frm.page.set_primary_action(__("Allocate Leave"), () => {
			frm.trigger("allocate_leave");
		});
	},

	allocate_leave(frm) {
		const check_map = frm.employees_datatable.rowmanager.checkMap;
		const selected_employees = [];
		check_map.forEach((is_checked, idx) => {
			if (is_checked)
				selected_employees.push(
					frm.employees_datatable.datamanager.data[idx].employee
				);
		});
		frm
			.call({
				method: "allocate_leave",
				doc: frm.doc,
				args: {
					employees: selected_employees,
				},
				freeze: true,
				freeze_message: __("Allocating Leave"),
			})
			.then((r) => {
				// don't refresh on complete failure
				if (r.message.failed && !r.message.success) return;
				frm.refresh();
			});
	},
});

const set_field_options = (frm) => {
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
			frm.trigger("load_employees");
		},
	});
};
