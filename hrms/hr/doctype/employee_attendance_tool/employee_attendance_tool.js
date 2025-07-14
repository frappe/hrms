frappe.ui.form.on("Employee Attendance Tool", {
	refresh(frm) {
		frm.trigger("reset_attendance_fields");
		frm.trigger("reset_tool_actions");
		hide_field("select_employees_section");
		hide_field("marked_attendance_section");
	},

	onload(frm) {
		frm.set_value("date", frappe.datetime.get_today());
	},

	date: function (frm) {
		hide_field("select_employees_section");
		hide_field("marked_attendance_section");
		frm.trigger("reset_tool_actions");
	},

	reset_tool_actions(frm) {
		frm.disable_save();
		get_employees_button = this.cur_frm.fields_dict.get_employees.$input;
		get_employees_button.removeClass("btn-default").addClass("btn-primary");
	},

	get_employees: function (frm) {
		frm.trigger("load_employees");
	},

	reset_attendance_fields(frm) {
		frm.set_value("status", "");
		frm.set_value("shift", "");
		frm.set_value("late_entry", 0);
		frm.set_value("early_exit", 0);
		frm.set_value("half_day_status", "");
	},

	load_employees(frm) {
		if (!frm.doc.date) return;
		frappe
			.call({
				method: "hrms.hr.doctype.employee_attendance_tool.employee_attendance_tool.get_employees",
				args: {
					date: frm.doc.date,
					department: frm.doc.department,
					branch: frm.doc.branch,
					company: frm.doc.company,
					employment_type: frm.doc.employment_type,
					designation: frm.doc.designation,
					employee_grade: frm.doc.employee_grade,
				},
				freeze: true,
				freeze_message: __("...Fetching Employees"),
			})
			.then((r) => {
				unmarked_employees = r.message["unmarked"].length;
				half_day_marked_employees = r.message["half_day_marked"].length;
				if (r.message["marked"].length > 0) {
					unhide_field("marked_attendance_section");
					frm.events.show_marked_employees(frm, r.message["marked"]);
				} else {
					hide_field("marked_attendance_section");
				}
				if (unmarked_employees > 0 || half_day_marked_employees > 0) {
					if (unmarked_employees) {
						unhide_field("status");
						unhide_field("unmarked_employee_header");
					} else {
						hide_field("status");
						hide_field("unmarked_employee_header");
					}
					frm.events.show_employees_to_mark(
						frm,
						"unmarked_employees_html",
						"unmarked_employees_multicheck",
						r.message["unmarked"],
					);
					if (half_day_marked_employees) {
						unhide_field("half_day_status");
						unhide_field("half_day_marked_employee_header");
					} else {
						hide_field("half_day_status");
						hide_field("half_day_marked_employee_header");
					}
					frm.events.show_employees_to_mark(
						frm,
						"half_marked_employees_html",
						"half_marked_employees_multicheck",
						r.message["half_day_marked"],
					);
					unmarked_employees && half_day_marked_employees
						? unhide_field("horizontal_break")
						: hide_field("horizontal_break");
					unhide_field("select_employees_section");
					frm.trigger("set_primary_action");
				} else {
					frappe.msgprint({
						message: __(
							"Attendance for all the employees under this criteria has been marked already.",
						),
						title: __("Attendance Marked"),
						indicator: "green",
					});
				}
			});
	},
	show_employees_to_mark(frm, html_fieldname, multicheck_fieldname, employee_list) {
		if (!employee_list.length) return;
		const $wrapper = frm.get_field(html_fieldname).$wrapper;
		$wrapper.empty();
		const employee_wrapper = $(`<div class="employee_wrapper">`).appendTo($wrapper);
		frm.fields_dict[multicheck_fieldname] = frappe.ui.form.make_control({
			parent: employee_wrapper,
			df: {
				fieldname: multicheck_fieldname,
				fieldtype: "MultiCheck",
				select_all: true,
				columns: 3,
				get_data: () => {
					return employee_list.map((employee) => {
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

		frm.get_field(multicheck_fieldname).refresh_input();
	},

	show_marked_employees(frm, marked_employees) {
		const $wrapper = frm.get_field("marked_attendance_html").$wrapper;
		const summary_wrapper = $(`<div class="summary_wrapper">`).appendTo($wrapper);
		const columns = frm.events.get_columns_for_marked_attendance_table(frm);
		const data = marked_employees.map((entry) => {
			return [`${entry.employee} : ${entry.employee_name}`, entry.status];
		});
		frm.events.render_marked_employee_datatable(frm, data, summary_wrapper, columns);
	},

	get_columns_for_marked_attendance_table() {
		return [
			{
				name: "employee",
				id: "employee",
				content: __("Employee"),
				width: 300,
			},
			{
				name: "status",
				id: "status",
				content: __("Status"),
				width: 100,
				format: (value) => {
					if (value == "Present" || value == "Work From Home")
						return `<span style="color:green">${__(value)}</span>`;
					else if (value == "Absent")
						return `<span style="color:red">${__(value)}</span>`;
					else if (value == "Half Day")
						return `<span style="color:orange">${__(value)}</span>`;
					else if (value == "On Leave")
						return `<span style="color:#318AD8">${__(value)}</span>`;
				},
			},
			{
				name: "shift",
				id: "shift",
				content: __("Shift"),
				width: 200,
			},
			{
				name: "leave_type",
				id: "leave_type",
				content: __("Leave Type"),
				width: 200,
			},
		].map((x) => ({
			...x,
			editable: false,
			sortable: false,
			focusable: false,
			dropdown: false,
			align: "left",
		}));
	},
	show_marked_employees(frm, marked_employees) {
		const $wrapper = frm.get_field("marked_attendance_html").$wrapper;
		const summary_wrapper = $(`<div class="summary_wrapper">`).appendTo($wrapper);

		const data = marked_employees.map((entry) => {
			return [
				`${entry.employee} : ${entry.employee_name}`,
				entry.status,
				entry.shift,
				entry.leave_type,
			];
		});

		frm.events.render_datatable(frm, data, summary_wrapper);
	},

	render_datatable(frm, data, summary_wrapper) {
		const columns = frm.events.get_columns_for_marked_attendance_table(frm);

		if (!frm.marked_emp_datatable) {
			const datatable_options = {
				columns: columns,
				data: data,
				dynamicRowHeight: true,
				inlineFilters: true,
				layout: "fixed",
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
	set_primary_action(frm) {
		get_employees_button = this.cur_frm.fields_dict.get_employees.$input;
		get_employees_button.removeClass("btn-primary").addClass("btn-default");
		frm.page.set_primary_action(__("Mark Attendance"), () => {
			const employees_to_mark_full_day =
				frm.get_field("unmarked_employees_multicheck")?.get_checked_options() || [];
			const employees_to_mark_half_day =
				frm.get_field("half_marked_employees_multicheck")?.get_checked_options() || [];

			if (
				employees_to_mark_full_day.length === 0 &&
				employees_to_mark_half_day.length === 0
			) {
				frappe.throw({
					message: __("Please select the employees you want to mark attendance for."),
					title: __("Mandatory"),
				});
			}

			if (employees_to_mark_full_day.length > 0 && !frm.doc.status) {
				frappe.throw({
					message: __("Please select the attendance status."),
					title: __("Mandatory"),
				});
			}
			if (employees_to_mark_half_day.length > 0 && !frm.doc.half_day_status) {
				frappe.throw({
					message: __("Please select half day attendance status."),
					title: __("Mandatory"),
				});
			}
			if (employees_to_mark_full_day.length > 0 || employees_to_mark_half_day.length > 0) {
				frm.events.mark_full_day_attendance(
					frm,
					employees_to_mark_full_day,
					employees_to_mark_half_day,
				);
			}
		});
	},

	mark_full_day_attendance(frm, employees_to_mark_full_day, employees_to_mark_half_day) {
		frappe
			.call({
				method: "hrms.hr.doctype.employee_attendance_tool.employee_attendance_tool.mark_employee_attendance",
				args: {
					employee_list: employees_to_mark_full_day,
					status: frm.doc.status,
					date: frm.doc.date,
					late_entry: frm.doc.late_entry,
					early_exit: frm.doc.early_exit,
					shift: frm.doc.shift,
					mark_half_day: employees_to_mark_half_day.length ? true : false,
					half_day_status: frm.doc.half_day_status,
					half_day_employee_list: employees_to_mark_half_day,
				},
				freeze: true,
				freeze_message: __("Marking Attendance"),
			})
			.then((r) => {
				if (!r.exc) {
					frappe.show_alert({
						message: __("Attendance marked successfully"),
						indicator: "green",
					});
					frm.refresh();
				}
			});
	},
});
