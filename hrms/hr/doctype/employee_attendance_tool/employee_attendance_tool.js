frappe.ui.form.on("Employee Attendance Tool", {
	refresh(frm) {
		frm.disable_save();
	},

	onload(frm) {
		frm.set_value("date", frappe.datetime.get_today());
		frm.trigger("load_employees");
		frm.trigger("set_primary_action");
	},

	date(frm) {
		frm.trigger("load_employees");
	},

	department(frm) {
		frm.trigger("load_employees");
	},

	branch(frm) {
		frm.trigger("load_employees");
	},

	company(frm) {
		frm.trigger("load_employees");
	},

	status(frm) {
		frm.trigger("set_primary_action");
	},

	load_employees(frm) {
		if (!frm.doc.date)
			return;

		frappe.call({
			method: "hrms.hr.doctype.employee_attendance_tool.employee_attendance_tool.get_employees",
			args: {
				date: frm.doc.date,
				department: frm.doc.department,
				branch: frm.doc.branch,
				company: frm.doc.company
			}
		}).then((r) => {
			if (r.message["unmarked"].length > 0) {
				unhide_field("unmarked_attendance_section");
				frm.employees = r.message["unmarked"];
				frm.events.show_unmarked_employees(frm, r.message["unmarked"]);
			} else {
				hide_field("unmarked_attendance_section");
			}

			if (r.message["marked"].length > 0) {
				unhide_field("marked_attendance_html");
				frm.events.show_marked_employees(frm, r.message["marked"]);
			} else {
				hide_field("marked_attendance_html");
			}
		});
	},

	show_unmarked_employees(frm, unmarked_employees) {
		const $wrapper = frm.get_field("employees_html").$wrapper;
		const employee_wrapper = $(`<div class="employee_wrapper">`).appendTo($wrapper);

		if (!frm.employees_multicheck) {
			frm.employees_multicheck = frappe.ui.form.make_control({
				parent: employee_wrapper,
				df: {
					fieldname: "employees_multicheck",
					fieldtype: "MultiCheck",
					select_all: true,
					columns: 4,
					get_data: () => {
						return unmarked_employees.map((employee) => {
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
		}
	},

	show_marked_employees(frm, marked_employees) {
		const $wrapper = frm.get_field("marked_attendance_html").$wrapper;
		const summary_wrapper = $(`<div class="summary_wrapper">`).appendTo($wrapper);

		frm.events.render_datatable(frm, marked_employees, summary_wrapper);
	},

	render_datatable(frm, data, summary_wrapper) {
		const columns = frm.events.get_columns_for_marked_attendance_table(frm);

		if (!frm.marked_emp_datatable) {
			const datatable_options = {
				columns: columns,
				data: data,
				dynamicRowHeight: true,
				inlineFilters: true,
				layout: "fluid",
				cellHeight: 35,
				noDataMessage: __("No Data"),
				disableReorderColumn: true,
			};
			frm.marked_emp_datatable = new frappe.DataTable(
				summary_wrapper.get(0),
				datatable_options,
			);
		} else {
			frm.marked_emp_datatable.refresh(data, columns);
		}
	},

	get_columns_for_marked_attendance_table(frm) {
		const status_map = [
			{"status": "Present", "indicator": "green"},
			{"status": "Absent", "indicator": "red"},
			{"status": "Half Day", "indicator": "orange"},
			{"status": "Work From Home", "indicator": "green"},
		];

		return status_map.map((entry) => {
			return {
				name: entry.status,
				id: entry.status,
				content: `<span class="indicator ${entry.indicator}">${__(entry.status)}</span>`,
				editable: false,
				sortable: false,
				focusable: false,
				dropdown: false,
				align: "left",
			}
		});
	},

	set_primary_action(frm) {
		frm.disable_save();

		if (frm.doc.status)
			frm.page.set_primary_action(__("Mark Attendance"), () => frm.trigger("mark_attendance"));
	},

	mark_attendance(frm) {
		const marked_employees = frm.employees_multicheck.get_checked_options();

		frappe.call({
			method: "hrms.hr.doctype.employee_attendance_tool.employee_attendance_tool.mark_employee_attendance",
			args: {
				employee_list: marked_employees,
				status: frm.doc.status,
				date: frm.doc.date,
				company: frm.doc.company
			},
			freeze: true,
			callback: function(r) {
				if (!r.exc) {
					frappe.show_alert({message: __("Attendance marked successfully"), indicator: "green"});
					frm.trigger("load_employees");
				}
			}
		});
	}
});
