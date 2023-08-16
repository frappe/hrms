// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on("Leave Control Panel", {
	onload: function (frm) {
		if (!frm.doc.from_date) {
			frm.set_value("from_date", frappe.datetime.get_today());
		}
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

	load_employees(frm) {
		frm
			.call({
				method: "get_employees",
				args: {
					company: frm.doc.company,
					employment_type: frm.doc.employment_type,
					branch: frm.doc.branch,
					department: frm.doc.department,
					designation: frm.doc.designation,
					grade: frm.doc.employee_grade,
				},
			})
			.then((r) => {
				frm.employees = r.message;
				frm.events.show_employees(frm, frm.employees);
			});
	},

	show_employees(frm, employees) {
		const $wrapper = frm.get_field("employees_html").$wrapper;
		frm.employee_wrapper = $(`<div class="employee_wrapper">`).appendTo(
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
			frm.employees_datatable.refresh(data, columns);
		}
	},

	get_columns_for_employees_table() {
		return [
			{
				name: "employee",
				id: "employee",
				content: `${__("Employee")}`,
			},
			{
				name: "employee_name",
				id: "employee_name",
				content: `${__("Name")}`,
			},
			{
				name: "company",
				id: "company",
				content: `${__("Company")}`,
			},
			{
				name: "department",
				id: "department",
				content: `${__("Department")}`,
			},
		].map((x) => ({
			...x,
			editable: false,
			focusable: false,
			dropdown: false,
			align: "left",
		}));
	},

	set_primary_action(frm) {
		frm.disable_save();
		frm.page.set_primary_action(__("Allocate Leave"), () => {
			frm.trigger("allocate_leave");
		});
	},

	allocate_leave(frm) {
		const selected_rows = [];
		frm.employee_wrapper.find(":input[type=checkbox]").each((idx, row) => {
			if (row.checked && idx > 0) {
				selected_rows.push(frm.employees[idx - 1].employee);
			}
		});
		frm
			.call({
				method: "allocate_leave",
				doc: frm.doc,
				args: {
					employees: selected_rows,
				},
				freeze: true,
				freeze_message: __("Allocating Leave"),
			})
			.then((r) => {
				if (!r.exc) {
					frappe.show_alert({
						message: __("Leave allocated successfully"),
						indicator: "green",
					});
					frm.refresh();
				}
			});
	},
});
