// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.listview_settings["Holiday List"] = {
	onload(list_view) {
		if (frappe.perm.has_perm("Holiday List Assignment", 0, "create")) {
			list_view.page.add_inner_button(__("Bulk Assignment"), () => {
				hrms.show_bulk_holiday_list_assignment_dialog(list_view);
			});
		}
	},
};

frappe.provide("hrms");

$.extend(hrms, {
	EMPLOYEE_FETCH_LIMIT: 500,

	show_bulk_holiday_list_assignment_dialog(list_view) {
		const dialog = new frappe.ui.Dialog({
			title: __("Bulk Holiday List Assignment"),
			size: "large",
			fields: [
				{
					fieldname: "holiday_list",
					fieldtype: "Link",
					label: __("Holiday List"),
					options: "Holiday List",
					reqd: 1,
					onchange: () => {
						hrms.set_holiday_list_dates(dialog);
						hrms.get_employees_for_bulk_assignment(dialog);
					},
				},
				{
					fieldname: "from_date",
					fieldtype: "Date",
					label: __("Assignment Starts From"),
					reqd: 1,
				},
				{ fieldtype: "Column Break" },
				{
					fieldname: "company",
					fieldtype: "Link",
					label: __("Company"),
					options: "Company",
					reqd: 1,
					default: frappe.defaults.get_default("company"),
					onchange: () => hrms.get_employees_for_bulk_assignment(dialog),
				},
				{
					fieldname: "quick_filters_section",
					fieldtype: "Section Break",
					label: __("Quick Filters"),
					collapsible: 1,
				},
				{
					fieldname: "branch",
					fieldtype: "Link",
					label: __("Branch"),
					options: "Branch",
					onchange: () => hrms.get_employees_for_bulk_assignment(dialog),
				},
				{
					fieldname: "department",
					fieldtype: "Link",
					label: __("Department"),
					options: "Department",
					onchange: () => hrms.get_employees_for_bulk_assignment(dialog),
				},
				{
					fieldname: "designation",
					fieldtype: "Link",
					label: __("Designation"),
					options: "Designation",
					onchange: () => hrms.get_employees_for_bulk_assignment(dialog),
				},
				{ fieldtype: "Column Break" },
				{
					fieldname: "grade",
					fieldtype: "Link",
					label: __("Employee Grade"),
					options: "Employee Grade",
					onchange: () => hrms.get_employees_for_bulk_assignment(dialog),
				},
				{
					fieldname: "employment_type",
					fieldtype: "Link",
					label: __("Employment Type"),
					options: "Employment Type",
					onchange: () => hrms.get_employees_for_bulk_assignment(dialog),
				},
				{
					fieldname: "clear_filters_html",
					fieldtype: "HTML",
				},
				{ fieldtype: "Section Break", label: __("Select Employees") },
				{
					fieldname: "employees_html",
					fieldtype: "HTML",
				},
			],
			primary_action_label: __("Assign Holiday List"),
			primary_action: () => hrms.bulk_assign_holiday_list(dialog, list_view),
		});

		dialog.show();
		hrms.render_clear_filters_button(dialog);
		hrms.set_employee_options(dialog, []);
	},

	render_clear_filters_button(dialog) {
		const $wrapper = dialog.get_field("clear_filters_html").$wrapper;
		$(`
			<div style="display: flex; justify-content: flex-end;">
				<button type="button" class="btn btn-xs btn-default clear-filters">
					${__("Clear Filters")}
				</button>
			</div>
		`)
			.appendTo($wrapper)
			.find(".clear-filters")
			.on("click", () => hrms.clear_quick_filters(dialog));
	},

	set_holiday_list_dates(dialog) {
		const holiday_list = dialog.get_value("holiday_list");
		if (!holiday_list) return dialog.set_value("from_date", null);

		frappe.db.get_value("Holiday List", holiday_list, "from_date", (r) => {
			dialog.set_value("from_date", r.from_date);
		});
	},

	clear_quick_filters(dialog) {
		const quick_filter_fields = [
			"branch",
			"department",
			"designation",
			"grade",
			"employment_type",
		];
		quick_filter_fields.forEach((fieldname) => dialog.set_value(fieldname, ""));
		hrms.get_employees_for_bulk_assignment(dialog);
	},

	get_filter_values(dialog) {
		const fieldnames = [
			"holiday_list",
			"from_date",
			"company",
			"branch",
			"department",
			"designation",
			"grade",
			"employment_type",
		];
		const filters = {};
		fieldnames.forEach((fieldname) => {
			filters[fieldname] = dialog.get_value(fieldname);
		});
		return filters;
	},

	get_employees_for_bulk_assignment(dialog) {
		const filters = hrms.get_filter_values(dialog);
		if (!filters.holiday_list) return hrms.set_employee_options(dialog, []);

		frappe
			.call({
				method: "hrms.hr.doctype.holiday_list_assignment.holiday_list_assignment.get_employees_for_bulk_assignment",
				args: { filters },
			})
			.then((r) => hrms.set_employee_options(dialog, r.message || []));
	},

	set_employee_options(dialog, employees) {
		const $wrapper = dialog.get_field("employees_html").$wrapper;
		$wrapper.empty();

		if (!employees.length) {
			const holiday_list = dialog.get_value("holiday_list");
			const message = holiday_list
				? __("All employees have already been assigned to this Holiday List.")
				: __("Please select a Holiday List.");
			$wrapper.append(
				`<div class="text-muted small" style="padding: 1em 0;">${message}</div>`,
			);
			return;
		}

		const $select_all_row = $(`
			<div style="margin-bottom: 0.5em;">
				<button type="button" class="btn btn-xs btn-default select-all">${__("Select All")}</button>
				<button type="button" class="btn btn-xs btn-default deselect-all">${__("Unselect All")}</button>
			</div>
		`).appendTo($wrapper);

		if (employees.length >= hrms.EMPLOYEE_FETCH_LIMIT) {
			$(`
				<div class="text-muted small" style="margin-bottom: 0.5em;">
					${__("Showing the first {0} matching employees. Use filters to narrow down the list.", [
						hrms.EMPLOYEE_FETCH_LIMIT,
					])}
				</div>
			`).appendTo($wrapper);
		}

		const $checkbox_area = $(`
			<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5em; max-height: 300px; overflow-y: auto;">
			</div>
		`).appendTo($wrapper);

		employees.forEach((emp) => {
			$(`
				<div class="checkbox">
					<label style="display: flex; align-items: center; gap: 0.5em; font-weight: normal;">
						<input type="checkbox" data-employee="${frappe.utils.escape_html(emp.employee)}" checked>
						<span>${frappe.utils.escape_html(emp.employee)}: ${frappe.utils.escape_html(
							emp.employee_name,
						)}</span>
					</label>
				</div>
			`).appendTo($checkbox_area);
		});

		$select_all_row.find(".select-all").on("click", () => {
			$checkbox_area.find('input[type="checkbox"]').prop("checked", true);
		});
		$select_all_row.find(".deselect-all").on("click", () => {
			$checkbox_area.find('input[type="checkbox"]').prop("checked", false);
		});

		dialog.employees_wrapper = $checkbox_area;
	},

	get_selected_employees(dialog) {
		if (!dialog.employees_wrapper) return [];
		return dialog.employees_wrapper
			.find('input[type="checkbox"]:checked')
			.map(function () {
				return $(this).attr("data-employee");
			})
			.get();
	},

	bulk_assign_holiday_list(dialog, list_view) {
		const filters = hrms.get_filter_values(dialog);
		const missing_fields = [];
		if (!filters.holiday_list) missing_fields.push(__("Holiday List"));
		if (!filters.from_date) missing_fields.push(__("Assignment Starts From"));
		if (!filters.company) missing_fields.push(__("Company"));

		if (missing_fields.length) {
			frappe.throw({
				message:
					__("Mandatory fields required for this action:") +
					"<br><br><ul><li>" +
					missing_fields.join("</li><li>") +
					"</ul>",
				title: __("Missing Fields"),
			});
		}

		const selected_employees = hrms.get_selected_employees(dialog).map((employee) => ({
			employee,
		}));

		if (!selected_employees.length) {
			frappe.throw({
				message: __("Please select at least one employee to perform this action."),
				title: __("No Employees Selected"),
			});
		}

		frappe.confirm(
			__("Assign Holiday List to {0} employee(s)?", [selected_employees.length]),
			() => {
				frappe.call({
					method: "hrms.hr.doctype.holiday_list_assignment.holiday_list_assignment.bulk_assign_holiday_list",
					args: {
						filters,
						employees: selected_employees,
					},
					freeze: true,
					freeze_message: __("Assigning Holiday List"),
					callback: () => {
						dialog.hide();
						list_view.refresh();
					},
				});
			},
		);
	},
});

frappe.realtime.on("completed_bulk_holiday_list_assignment", (message) => {
	if (message.success && message.success.length) {
		frappe.show_alert({
			message: __("{0} Holiday List Assignment(s) created", [message.success.length]),
			indicator: "green",
		});
	}

	if (message.failure && message.failure.length) {
		frappe.msgprint({
			message: __("Failed to create Holiday List Assignment for employees: {0}", [
				frappe.utils.comma_and(message.failure),
			]),
			title: __("Failure"),
			indicator: "red",
		});
	}
});
