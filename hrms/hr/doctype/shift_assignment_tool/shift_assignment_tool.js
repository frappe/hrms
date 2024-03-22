// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shift Assignment Tool", {
	setup(frm) {
		hrms.setup_employee_filter_group(frm);
	},

	async refresh(frm) {
		frm.trigger("set_primary_action");
		frm.trigger("handle_realtime");
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
		if (frm.doc.end_date < frm.doc.start_date)
			frm.set_value("start_date", null);
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
		frm.page.set_primary_action(__("Assign Shift"), () => {
			frm.trigger("assign_shift");
		});
	},

	handle_realtime(frm) {
		frappe.realtime.off("completed_bulk_shift_assignment");
		frappe.realtime.on("completed_bulk_shift_assignment", (message) => {
			hrms.notify_bulk_action_status(
				"Shift Assignment",
				message.failure,
				message.success
			);

			// refresh only on complete/partial success
			if (message.success) frm.refresh();
		});
	},

	get_employees(frm) {
		if (!(frm.doc.shift_type && frm.doc.start_date))
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
		const columns = frm.events.employees_datatable_columns();
		const no_data_message = __(
			frm.doc.shift_type && frm.doc.start_date
				? "There are no employees without Shift Assignments for these dates based on the given filters."
				: "Please select Shift Type and assignment date(s)."
		);
		hrms.render_employees_datatable(frm, columns, employees, no_data_message);
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

	assign_shift(frm) {
		const rows = frm.employees_datatable.datamanager.data;
		const selected_employees = [];
		const checked_row_indexes =
			frm.employees_datatable.rowmanager.getCheckedRows();
		checked_row_indexes.forEach((idx) => {
			selected_employees.push(rows[idx].employee);
		});

		frappe.confirm(__("Assign Shift to selected employees?"), () => {
			frm.events.bulk_assign_shift(frm, selected_employees);
		});
	},

	bulk_assign_shift(frm, employees) {
		frm.call({
			method: "bulk_assign_shift",
			doc: frm.doc,
			args: {
				employees: employees,
			},
			freeze: true,
			freeze_message: __("Assigning Shift"),
		});
	},
});
