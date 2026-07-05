// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bulk Holiday List Assignment", {
	setup(frm) {
		frm.trigger("set_queries");
		hrms.setup_employee_filter_group(frm);
	},

	refresh(frm) {
		frm.page.clear_indicator();
		frm.disable_save();
		frm.trigger("set_primary_action");
		frm.trigger("get_employees");
		hrms.handle_realtime_bulk_action_notification(
			frm,
			"completed_bulk_holiday_list_assignment",
			"Holiday List Assignment",
		);
	},

	holiday_list(frm) {
		frm.trigger("set_from_date");
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

	designation(frm) {
		frm.trigger("get_employees");
	},

	employment_type(frm) {
		frm.trigger("get_employees");
	},

	grade(frm) {
		frm.trigger("get_employees");
	},

	set_queries(frm) {
		frm.set_query("department", function () {
			return {
				filters: {
					company: frm.doc.company,
				},
			};
		});
	},

	set_from_date(frm) {
		if (!frm.doc.holiday_list) return;
		frappe.db.get_value("Holiday List", frm.doc.holiday_list, "from_date", (r) => {
			frm.set_value("from_date", r.from_date);
		});
	},

	set_primary_action(frm) {
		frm.page.set_primary_action(__("Assign Holiday List"), () => {
			frm.trigger("assign_holiday_list");
		});
	},

	get_employees(frm) {
		if (!frm.doc.holiday_list || !frm.doc.from_date)
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
		const columns = frm.events.get_employees_datatable_columns();
		const no_data_message = __(
			frm.doc.holiday_list && frm.doc.from_date
				? "There are no employees without a Holiday List Assignment on this date based on the given filters."
				: "Please select Holiday List and Assignment Starts From date.",
		);

		hrms.render_employees_datatable(frm, columns, employees, no_data_message);
	},

	get_employees_datatable_columns() {
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
				name: "department",
				id: "department",
				content: __("Department"),
			},
			{
				name: "designation",
				id: "designation",
				content: __("Designation"),
			},
		].map((x) => ({
			...x,
			editable: false,
			focusable: false,
			dropdown: false,
			align: "left",
		}));
	},

	assign_holiday_list(frm) {
		const check_map = frm.employees_datatable.rowmanager.checkMap;
		const selected_employees = [];
		check_map.forEach((is_checked, idx) => {
			if (is_checked)
				selected_employees.push(frm.employees_datatable.datamanager.data[idx].employee);
		});

		hrms.validate_mandatory_fields(frm, selected_employees);

		frappe.confirm(
			__("Assign Holiday List to {0} employee(s)?", [selected_employees.length]),
			() => frm.events.bulk_assign_holiday_list(frm, selected_employees),
		);
	},

	bulk_assign_holiday_list(frm, employees) {
		frm.call({
			method: "bulk_assign_holiday_list",
			doc: frm.doc,
			args: {
				employees: employees,
			},
			freeze: true,
			freeze_message: __("Assigning Holiday List"),
		});
	},
});
