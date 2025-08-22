// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on("Leave Control Panel", {
	setup: function (frm) {
		frm.trigger("set_query");
		frm.trigger("set_leave_details");
		hrms.setup_employee_filter_group(frm);
	},

	refresh: function (frm) {
		frm.page.clear_indicator();
		frm.disable_save();
		frm.trigger("get_employees");
		frm.trigger("set_primary_action");
		hrms.handle_realtime_bulk_action_notification(
			frm,
			"completed_bulk_leave_policy_assignment",
			"Leave Policy Assignment",
		);
		hrms.handle_realtime_bulk_action_notification(
			frm,
			"completed_bulk_leave_allocation",
			"Leave Allocation",
		);
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
		frm.trigger("get_employees");
	},

	employment_type(frm) {
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

	employee_grade(frm) {
		frm.trigger("get_employees");
	},

	dates_based_on(frm) {
		frm.trigger("reset_leave_details");
		frm.trigger("get_employees");
	},

	from_date(frm) {
		frm.trigger("get_employees");
	},

	to_date(frm) {
		frm.trigger("get_employees");
	},

	leave_period(frm) {
		frm.trigger("get_employees");
	},

	allocate_based_on_leave_policy(frm) {
		frm.trigger("get_employees");
	},

	leave_type(frm) {
		frm.trigger("get_employees");
	},

	leave_policy(frm) {
		frm.trigger("get_employees");
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

	get_employees(frm) {
		frm.call({
			method: "get_employees",
			args: {
				advanced_filters: frm.advanced_filters || [],
			},
			doc: frm.doc,
		}).then((r) => {
			const columns = frm.events.get_employees_datatable_columns();
			hrms.render_employees_datatable(frm, columns, r.message);
		});
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
				selected_employees.push(frm.employees_datatable.datamanager.data[idx].employee);
		});

		hrms.validate_mandatory_fields(frm, selected_employees);

		frappe.confirm(
			__("Allocate leaves to {0} employee(s)?", [selected_employees.length]),
			() => frm.events.bulk_allocate_leave(frm, selected_employees),
		);
	},

	bulk_allocate_leave(frm, employees) {
		frm.call({
			method: "allocate_leave",
			doc: frm.doc,
			args: {
				employees: employees,
			},
			freeze: true,
			freeze_message: __("Allocating Leave"),
		}).then((r) => {
			// don't refresh on complete failure
			if (r.message.failed && !r.message.success) return;
			frm.refresh();
		});
	},
});
