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
				if (r.message.length > 0) {
					unhide_field("select_employees_section");
					frm.events.show_employees(frm, r.message);
				} else {
					hide_field("select_employees_section");
				}
			});
	},

	show_employees(frm, employees) {
		const $wrapper = frm.get_field("employees_html").$wrapper;
		$wrapper.empty();
		const employee_wrapper = $(`<div class="employee_wrapper">`).appendTo(
			$wrapper
		);
		frm.employees_multicheck = frappe.ui.form.make_control({
			parent: employee_wrapper,
			df: {
				fieldname: "employees_multicheck",
				fieldtype: "MultiCheck",
				select_all: true,
				columns: 4,
				get_data: () => {
					return employees.map((employee) => {
						return {
							label: `${employee.employee} : ${employee.employee_name}`,
							value: employee.employee,
							checked: 0,
						};
					});
				},
			},
			render_input: true,
		});
		frm.employees_multicheck.refresh_input();
	},

	set_primary_action(frm) {
		frm.disable_save();
		frm.page.set_primary_action(__("Allocate Leave"), () => {
			frm.trigger("allocate_leave");
		});
	},

	allocate_leave(frm) {
		const selected_employees = frm.employees_multicheck.get_checked_options();
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
