// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shift Assignment Tool", {
	setup(frm) {
		hrms.setup_employee_filter_group(frm);
	},

	refresh(frm) {
		frm.page.clear_indicator();
		frm.disable_save();
		frm.trigger("set_primary_action");
		frm.trigger("get_employees");

		hrms.handle_realtime_bulk_action_notification(
			frm,
			"completed_bulk_shift_assignment",
			"Shift Assignment",
		);
		hrms.handle_realtime_bulk_action_notification(
			frm,
			"completed_bulk_shift_schedule_assignment",
			"Shift Schedule Assignment",
		);
		hrms.handle_realtime_bulk_action_notification(
			frm,
			"completed_bulk_shift_request_processing",
			"Shift Request",
		);
	},

	action(frm) {
		frm.trigger("set_primary_action");
		frm.trigger("get_employees");
	},

	company(frm) {
		frm.trigger("get_employees");
	},

	shift_type(frm) {
		frm.trigger("get_employees");
	},

	status(frm) {
		frm.trigger("get_employees");
	},

	start_date(frm) {
		if (frm.doc.start_date > frm.doc.end_date) frm.set_value("end_date", null);
		frm.trigger("get_employees");
	},

	end_date(frm) {
		if (frm.doc.end_date < frm.doc.start_date) frm.set_value("start_date", null);
		frm.trigger("get_employees");
	},

	shift_type_filter(frm) {
		frm.trigger("get_employees");
	},

	shift_schedule(frm) {
		frm.trigger("get_employees");
	},

	approver(frm) {
		frm.trigger("get_employees");
	},

	from_date(frm) {
		if (frm.doc.from_date > frm.doc.to_date) frm.set_value("to_date", null);
		frm.trigger("get_employees");
	},

	to_date(frm) {
		if (frm.doc.to_date < frm.doc.from_date) frm.set_value("from_date", null);
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
		const select_rows_section_head = document
			.querySelector('[data-fieldname="select_rows_section"]')
			.querySelector(".section-head");
		select_rows_section_head.textContent = __("Select Employees");
		frm.clear_custom_buttons();
		frm.page.clear_primary_action();

		if (frm.doc.action === "Assign Shift")
			frm.page.set_primary_action(__("Assign Shift"), () => {
				frm.trigger("bulk_assign");
			});
		else if (frm.doc.action === "Assign Shift Schedule")
			frm.page.set_primary_action(__("Assign Shift Schedule"), () => {
				frm.trigger("bulk_assign");
			});
		else {
			frm.page.add_inner_button(
				__("Approve"),
				() => {
					frm.events.process_shift_requests(frm, "Approved");
				},
				__("Process Requests"),
			);
			frm.page.add_inner_button(
				__("Reject"),
				() => {
					frm.events.process_shift_requests(frm, "Rejected");
				},
				__("Process Requests"),
			);
			frm.page.set_inner_btn_group_as_primary(__("Process Requests"));
			frm.page.clear_menu();
			select_rows_section_head.textContent = __("Select Shift Requests");
		}
	},

	get_employees(frm) {
		if (
			(frm.doc.action === "Assign Shift" && !(frm.doc.shift_type && frm.doc.start_date)) ||
			(frm.doc.action === "Assign Shift Schedule" &&
				!(frm.doc.shift_schedule && frm.doc.start_date))
		)
			return frm.events.render_employees_datatable(frm, []);

		frm.call({
			method: "get_employees",
			args: {
				advanced_filters: frm.advanced_filters || [],
			},
			doc: frm.doc,
		}).then((r) => frm.events.render_employees_datatable(frm, r.message));
	},

	render_employees_datatable(frm, employees) {
		let columns = undefined;
		let no_data_message = undefined;
		if (frm.doc.action === "Assign Shift") {
			columns = frm.events.get_assign_shift_datatable_columns();
			no_data_message = __(
				frm.doc.shift_type && frm.doc.start_date
					? "There are no employees without Shift Assignments for these dates based on the given filters."
					: "Please select Shift Type and assignment date(s).",
			);
		} else if (frm.doc.action === "Assign Shift Schedule") {
			columns = frm.events.get_assign_shift_datatable_columns();
			no_data_message = __(
				frm.doc.shift_schedule && frm.doc.start_date
					? "There are no employees without active overlapping Shift Schedule Assignments based on the given filters."
					: "Please select Shift Schedule and assignment date(s).",
			);
		} else {
			columns = frm.events.get_process_shift_requests_datatable_columns();
			no_data_message = "There are no open Shift Requests based on the given filters.";
		}
		hrms.render_employees_datatable(frm, columns, employees, no_data_message);
	},

	get_assign_shift_datatable_columns() {
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
				name: "branch",
				id: "branch",
				content: __("Branch"),
			},
			{
				name: "department",
				id: "department",
				content: __("Department"),
			},
			{
				name: "default_shift",
				id: "default_shift",
				content: __("Default Shift"),
			},
		].map((x) => ({
			...x,
			editable: false,
			focusable: false,
			dropdown: false,
			align: "left",
		}));
	},

	get_process_shift_requests_datatable_columns() {
		return [
			{
				name: "shift_request",
				id: "shift_request",
				content: __("Shift Request"),
			},
			{
				name: "employee",
				id: "employee_name",
				content: __("Employee"),
			},
			{
				name: "shift_type",
				id: "shift_type",
				content: __("Shift Type"),
			},
			{
				name: "from_date",
				id: "from_date",
				content: __("From Date"),
			},
			{
				name: "to_date",
				id: "to_date",
				content: __("To Date"),
			},
		].map((x) => ({
			...x,
			editable: false,
			focusable: false,
			dropdown: false,
			align: "left",
		}));
	},

	bulk_assign(frm, employees) {
		const rows = frm.employees_datatable.datamanager.data;
		const selected_employees = [];
		const checked_row_indexes = frm.employees_datatable.rowmanager.getCheckedRows();
		checked_row_indexes.forEach((idx) => {
			selected_employees.push(rows[idx].employee);
		});

		hrms.validate_mandatory_fields(frm, selected_employees);
		frappe.confirm(
			__("{0} to {1} employee(s)?", [__(frm.doc.action), selected_employees.length]),
			() => {
				frm.call({
					method: "bulk_assign",
					doc: frm.doc,
					args: {
						employees: selected_employees,
					},
					freeze: true,
					freeze_message: __("Assigning..."),
				});
			},
		);
	},

	process_shift_requests(frm, status) {
		const rows = frm.employees_datatable.datamanager.data;
		const selected_requests = [];
		const checked_row_indexes = frm.employees_datatable.rowmanager.getCheckedRows();
		checked_row_indexes.forEach((idx) => {
			selected_requests.push({
				shift_request: rows[idx].name,
				employee: rows[idx].employee,
			});
		});

		hrms.validate_mandatory_fields(frm, selected_requests, "Shift Requests");
		frappe.confirm(
			__("Process {0} Shift Request(s) as <b>{1}</b>?", [selected_requests.length, status]),
			() => {
				frm.events.bulk_process_shift_requests(frm, selected_requests, status);
			},
		);
	},

	bulk_process_shift_requests(frm, shift_requests, status) {
		frm.call({
			method: "bulk_process_shift_requests",
			doc: frm.doc,
			args: {
				shift_requests: shift_requests,
				status: status,
			},
			freeze: true,
			freeze_message: __("Processing Requests"),
		});
	},
});
