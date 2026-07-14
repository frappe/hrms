// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Leave Policy", {
	refresh: function (frm) {
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(
				__("Assign to Employees"),
				() => frm.events.assign_to_employees(frm),
				__("Actions"),
			);
		}
	},

	assign_to_employees: function (frm) {
		// Bulk-assign this leave policy to many employees at once. The picker also
		// collects the assignment parameters the Leave Policy master doesn't carry.
		hrms.assign_to_employees({
			title: __("Assign Leave Policy to Employees"),
			data_fields: [
				{
					fieldname: "assignment_based_on",
					label: __("Assignment Based On"),
					fieldtype: "Select",
					options: ["", "Leave Period", "Joining Date"].join("\n"),
				},
				{
					fieldname: "leave_period",
					label: __("Leave Period"),
					fieldtype: "Link",
					options: "Leave Period",
					depends_on: "eval:doc.assignment_based_on == 'Leave Period'",
					get_query: () => {
						return { filters: { is_active: 1 } };
					},
				},
				{
					fieldname: "effective_from",
					label: __("Effective From"),
					fieldtype: "Date",
					depends_on: "eval:doc.assignment_based_on != 'Leave Period'",
				},
				{
					fieldname: "effective_to",
					label: __("Effective To"),
					fieldtype: "Date",
					depends_on: "eval:doc.assignment_based_on != 'Leave Period'",
				},
				{
					fieldname: "carry_forward",
					label: __("Carry Forward"),
					fieldtype: "Check",
				},
			],
			on_assign: (employees, values) => {
				// validate assignment parameters before hitting the server
				if (values.assignment_based_on === "Leave Period" && !values.leave_period) {
					frappe.msgprint(__("Please select a Leave Period."));
					return false;
				}
				if (
					!["Leave Period", "Joining Date"].includes(values.assignment_based_on) &&
					(!values.effective_from || !values.effective_to)
				) {
					frappe.msgprint(__("Please set Effective From and Effective To dates."));
					return false;
				}

				return frappe
					.call({
						method: "hrms.hr.doctype.leave_policy_assignment.leave_policy_assignment.create_assignment_for_multiple_employees",
						args: {
							employees: employees,
							data: {
								assignment_based_on: values.assignment_based_on || "",
								leave_policy: frm.doc.name,
								effective_from: values.effective_from,
								effective_to: values.effective_to,
								leave_period: values.leave_period,
								carry_forward: values.carry_forward ? 1 : 0,
							},
						},
						freeze: true,
						freeze_message: __("Assigning Leave Policy to employees…"),
					})
					.then((r) => {
						const assigned = (r.message || []).length;
						if (assigned) {
							frappe.show_alert({
								message: __("Leave Policy assigned to {0} employee(s)", [
									assigned,
								]),
								indicator: "green",
							});
						}
					});
			},
		});
	},
});

frappe.ui.form.on("Leave Policy Detail", {
	leave_type: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.leave_type) {
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Leave Type",
					fieldname: "max_leaves_allowed",
					filters: { name: child.leave_type },
				},
				callback: function (r) {
					if (r.message) {
						child.annual_allocation = r.message.max_leaves_allowed;
						refresh_field("leave_policy_details");
					}
				},
			});
		} else {
			child.annual_allocation = "";
			refresh_field("leave_policy_details");
		}
	},
});
