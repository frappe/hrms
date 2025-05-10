frappe.ui.form.on("Employee Attendance Tool", {
	refresh(frm) {
		frm.trigger("reset_attendance_fields");
		frm.trigger("load_employees");
		frm.trigger("set_primary_action");
	},

	onload(frm) {
		frm.set_value("date", frappe.datetime.get_today());
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
	employement_type(frm) {
		frm.trigger("load_employees");
	},
	designation(frm) {
		frm.trigger("load_employees");
	},
	employee_grade(frm) {
		frm.trigger("load_employees");
	},
	status(frm) {
		frm.trigger("set_primary_action");
	},

	reset_attendance_fields(frm) {
		frm.set_value("status", "");
		frm.set_value("shift", "");
		frm.set_value("late_entry", 0);
		frm.set_value("early_exit", 0);
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
					employment_type: frm.employement_type,
					designation: frm.doc.designation,
					employee_grade: frm.doc.employee_grade,
				},
				freeze: true,
				freeze_message: __("...Feching Employees"),
			})
			.then((r) => {
				frm.no_employees_to_mark =
					r.message["unmarked"].length > 0 || r.message["half_day_marked"].length > 0
						? false
						: true;
				if (r.message["unmarked"].length > 0) {
					unhide_field("unmarked_attendance_section");
					unhide_field("attendance_details_section");
					frm.events.show_unmarked_employees(frm, r.message["unmarked"]);
				} else {
					hide_field("unmarked_attendance_section");
					hide_field("attendance_details_section");
				}
				if (r.message["half_day_marked"].length > 0) {
					unhide_field("half_day_attendance_section");
					unhide_field("attendance_details_section");
					frm.events.show_half_marked_employees(frm, r.message["half_day_marked"]);
				} else {
					hide_field("half_day_attendance_section");
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
		no_data_message = __(
			"Attendance for all the employees under this criteria has been marked already.",
		);
		frm.events.render_employees_datatable(
			frm,
			unmarked_employees,
			"unmarked_employees_html",
			"unmarked_employees_table",
			no_data_message,
			frm.events.get_columns_for_unmarked_employees_table,
		);
	},
	show_half_marked_employees(frm, half_marked_employees) {
		no_data_message = __(
			"Half Day Status for all the employees under this criteria has been marked already.",
		);
		frm.events.render_employees_datatable(
			frm,
			half_marked_employees,
			"half_marked_employees_html",
			"half_marked_employees_table",
			no_data_message,
			frm.events.get_columns_for_half_marked_employees_table,
		);
	},
	render_employees_datatable(
		frm,
		employees,
		html_field_name,
		datatable_name,
		no_data_message,
		get_columns_callback,
	) {
		const $wrapper = frm.get_field(html_field_name).$wrapper;
		const employee_wrapper = $(`<div class="employee_wrapper">`).appendTo($wrapper);
		const columns = get_columns_callback();
		const data = employees.map((entry) => {
			return Object.values(entry);
		});
		if (!frm.get_field(datatable_name)) {
			const datatable_options = {
				columns: columns,
				data: data,
				checkboxColumn: true,
				serialNoColumn: false,
				checkedRowStatus: false,
				dynamicRowHeight: true,
				inlineFilters: true,
				layout: "fixed",
				cellHeight: 35,
				noDataMessage: __(no_data_message),
				disableReorderColumn: true,
			};
			frm.fields_dict[datatable_name] = new frappe.DataTable(
				employee_wrapper.get(0),
				datatable_options,
			);
		} else {
			frm.get_field(datatable_name).rowmanager.checkMap = [];
			frm.get_field(datatable_name).refresh(data, columns);
		}
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

	get_columns_for_unmarked_employees_table() {
		return [
			{
				name: "employee",
				id: "employee",
				content: __("Employee"),
			},
			{
				name: "employee_name",
				id: "employee_name",
				content: __("Employee Name"),
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
			width: 200,
		}));
	},
	get_columns_for_half_marked_employees_table() {
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
				name: "status",
				id: "status",
				content: __("Status"),
				format: (value) => {
					return `<span style="color:orange">${__(value)}</span>`;
				},
			},
			{
				name: "leave_type",
				id: "leave_type",
				content: __("Leave Type"),
			},
		].map((x) => ({
			...x,
			editable: false,
			focusable: false,
			dropdown: false,
			align: "left",
			width: 200,
		}));
	},
	render_marked_employee_datatable(frm, data, summary_wrapper, columns) {
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
	get_columns_for_marked_attendance_table() {
		return [
			{
				name: "employee",
				id: "employee",
				content: __("Employee"),
				width: 350,
			},
			{
				name: "status",
				id: "status",
				content: __("Status"),
				width: 150,
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
		].map((x) => ({
			...x,
			editable: false,
			sortable: false,
			focusable: false,
			dropdown: false,
			align: "left",
		}));
	},

	set_primary_action(frm) {
		frm.disable_save();
		frm.page.set_primary_action(__("Mark Attendance"), () => {
			if (frm.no_employees_to_mark) {
				frappe.msgprint({
					message: __(
						"Attendance for all the employees under this criteria has been marked already.",
					),
					title: __("Attendance Marked"),
					indicator: "green",
				});
				return;
			}
			const unmarked_employees_check_map = frm.get_field("unmarked_employees_table")
				.rowmanager.checkMap;
			const half_day_employees_check_map = frm.get_field("half_marked_employees_table")
				.rowmanager.checkMap;
			const selected_employees_to_mark_full_day = [];
			const selected_employees_to_mark_half_day = [];
			unmarked_employees_check_map.forEach((is_checked, idx) => {
				if (is_checked)
					selected_employees_to_mark_full_day.push(
						frm.get_field("unmarked_employees_table").datamanager.data[idx][0],
					);
			});
			half_day_employees_check_map.forEach((is_checked, idx) => {
				if (is_checked)
					selected_employees_to_mark_half_day.push(
						frm.get_field("half_marked_employees_table").datamanager.data[idx][0],
					);
			});

			if (
				selected_employees_to_mark_full_day.length === 0 &&
				selected_employees_to_mark_half_day.length === 0
			) {
				frappe.throw({
					message: __("Please select the employees you want to mark attendance for."),
					title: __("Mandatory"),
				});
			}

			if (selected_employees_to_mark_full_day.length > 0 && !frm.doc.status) {
				frappe.throw({
					message: __("Please select the attendance status."),
					title: __("Mandatory"),
				});
			}
			if (selected_employees_to_mark_half_day.length > 0 && !frm.doc.half_day_status) {
				frappe.throw({
					message: __("Please select half day attendance status."),
					title: __("Mandatory"),
				});
			}
			if (
				selected_employees_to_mark_full_day.length > 0 ||
				selected_employees_to_mark_half_day > 0
			) {
				frm.events.mark_full_day_attendance(
					frm,
					selected_employees_to_mark_full_day,
					selected_employees_to_mark_half_day,
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
