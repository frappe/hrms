// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bulk Holiday List Assignment", {
	setup(frm) {},

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
		if (frm.doc.holiday_list) {
			frappe.db.get_value("Holiday List", frm.doc.holiday_list, "from_date", (r) => {
				frm.set_value("from_date", r.from_date);
			});
		} else {
			frm.set_value("from_date", null);
		}
		frm.trigger("get_employees");
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

	employment_type(frm) {
		frm.trigger("get_employees");
	},

	designation(frm) {
		frm.trigger("get_employees");
	},

	grade(frm) {
		frm.trigger("get_employees");
	},

	set_primary_action(frm) {
		frm.page.set_primary_action(__("Assign Holiday List"), () => {
			frm.trigger("bulk_assign");
		});
	},

	get_employees(frm) {
		if (!frm.doc.holiday_list) {
			return frm.events.render_employees_datatable(frm, []);
		}

		frm.call({
			method: "get_employees",
			doc: frm.doc,
		}).then((r) => frm.events.render_employees_datatable(frm, r.message));
	},

	render_employees_datatable(frm, employees) {
		frm.checked_rows_indexes = [];

		const columns = frm.events.get_employees_datatable_columns();
		const no_data_message = __(
			frm.doc.holiday_list
				? "All employees have already been assigned to this Holiday List."
				: "Please select a Holiday List.",
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
				content: __("Employee Name"),
			},
			{
				name: "department",
				id: "department",
				content: __("Department"),
			},
			{
				name: "branch",
				id: "branch",
				content: __("Branch"),
			},
		].map((x) => ({
			...x,
			editable: false,
			focusable: false,
			dropdown: false,
			align: "left",
		}));
	},

	bulk_assign(frm) {
		const rows = frm.employees_datatable.datamanager.data;
		const selected_employees = [];
		const checked_row_indexes = frm.employees_datatable.rowmanager.getCheckedRows();
		checked_row_indexes.forEach((idx) => {
			selected_employees.push({ employee: rows[idx].employee });
		});

		hrms.validate_mandatory_fields(frm, selected_employees);
		frappe.confirm(
			__("Assign Holiday List to {0} employee(s)?", [selected_employees.length]),
			() => {
				frm.call({
					method: "bulk_assign",
					doc: frm.doc,
					args: {
						employees: selected_employees,
					},
					freeze: true,
					freeze_message: __("Assigning Holiday List"),
				});
			},
		);
	},
});
