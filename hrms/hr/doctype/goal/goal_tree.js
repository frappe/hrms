frappe.provide("frappe.treeview_settings");

frappe.treeview_settings["Goal"] = {
	get_tree_nodes: "hrms.hr.doctype.goal.goal.get_children",
	filters: [
		{
			fieldname: "company",
			fieldtype: "Select",
			options: erpnext.utils.get_tree_options("company"),
			label: __("Company"),
			default: erpnext.utils.get_tree_default("company"),
		},
		{
			fieldname: "appraisal_cycle",
			fieldtype: "Link",
			options: "Appraisal Cycle",
			label: __("Appraisal Cycle"),
			get_query() {
				const company =
					frappe.treeview_settings["Goal"].page.fields_dict.company.get_value();

				return {
					filters: {
						company: company,
					},
				};
			},
		},
		{
			fieldname: "employee",
			fieldtype: "Link",
			options: "Employee",
			label: __("Employee"),
		},
		{
			fieldname: "date_range",
			fieldtype: "DateRange",
			label: __("Date Range"),
		},
	],
	fields: [
		{
			fieldtype: "Data",
			fieldname: "goal_name",
			label: __("Goal"),
			reqd: 1,
		},
		{
			fieldtype: "Check",
			fieldname: "is_group",
			label: __("Is Group"),
			description: __("Child nodes can only be created under 'Group' type nodes"),
		},
		{
			fieldtype: "Section Break",
		},
		{
			fieldtype: "Link",
			fieldname: "employee",
			label: __("Employee"),
			options: "Employee",
			reqd: 1,
			default() {
				const treeview = frappe.treeview_settings["Goal"].treeview;
				let employee =
					treeview.tree.get_selected_node().data.employee ||
					treeview.tree.session_employee ||
					"";

				return employee;
			},
		},
		{
			fieldtype: "Percent",
			fieldname: "progress",
			label: __("Progress"),
		},
		{
			fieldtype: "Column Break",
		},
		{
			fieldtype: "Date",
			fieldname: "start_date",
			label: __("Start Date"),
			reqd: 1,
			default: frappe.datetime.month_start(),
		},
		{
			fieldtype: "Date",
			fieldname: "end_date",
			label: __("End Date"),
			default: frappe.datetime.month_end(),
		},
		{
			fieldtype: "Section Break",
			label: __("Appraisal Linking"),
			description: __(
				"Link the cycle and tag KRA to your goal to update the appraisal's goal score based on the goal progress",
			),
			depends_on: "eval:doc.employee",
		},
		{
			fieldtype: "Link",
			fieldname: "appraisal_cycle",
			label: __("Appraisal Cycle"),
			options: "Appraisal Cycle",
			get_query() {
				const company =
					frappe.treeview_settings["Goal"].page.fields_dict.company.get_value();

				return {
					filters: {
						company: company,
						status: ["!=", "Completed"],
					},
				};
			},
			default() {
				const treeview = frappe.treeview_settings["Goal"].treeview;
				let appraisal_cycle =
					treeview.page.fields_dict.appraisal_cycle.get_value() ||
					treeview.tree.get_selected_node().data.appraisal_cycle ||
					"";

				return appraisal_cycle;
			},
		},
		{
			fieldtype: "Column Break",
		},
		{
			fieldtype: "Link",
			fieldname: "kra",
			label: __("KRA"),
			options: "KRA",
			mandatory_depends_on: "eval:doc.appraisal_cycle && !doc.parent_goal",
			get_query() {
				return {
					query: "hrms.hr.doctype.appraisal.appraisal.get_kras_for_employee",
					filters: {
						employee: cur_dialog.get_value("employee"),
						appraisal_cycle: cur_dialog.get_value("appraisal_cycle"),
					},
				};
			},
			default() {
				const treeview = frappe.treeview_settings["Goal"].treeview;
				return treeview.tree.get_selected_node().data.kra;
			},
		},
		{
			fieldtype: "Section Break",
			fieldname: "description_section",
			label: __("Description"),
			collapsible: 1,
			depends_on: "eval:doc.employee",
		},
		{
			fieldtype: "Text Editor",
			fieldname: "description",
		},
	],
	onload(treeview) {
		frappe.treeview_settings["Goal"].page = {};
		$.extend(frappe.treeview_settings["Goal"].page, treeview.page);
		treeview.make_tree();

		// set the current session employee
		frappe.db
			.get_value("Employee", { user_id: frappe.session.user }, "name")
			.then((employee_record) => {
				treeview.tree.session_employee = employee_record?.message?.name;
			});
	},
	onrender(node) {
		// show KRA against the goal
		if (node.data.kra) {
			$(node.$tree_link).find(".tree-label").append(`
				<span
					class="pill small"
					style="background-color: var(--bg-light-gray); color: var(--text-on-gray);">
					${node.data.kra}
				</span>
			`);
		}

		// show goal completion status
		if (node.data.completion_count !== undefined) {
			$(`
				<span class="balance-area pull-right text-muted small">
				${node.data.completion_count}
				</span>
			`).insertBefore(node.$ul);
		} else if (node.data && node.data.status !== undefined) {
			const status_color = {
				Pending: "yellow",
				"In Progress": "orange",
				Completed: "green",
				Archived: "gray",
			};
			$(`
				<span
					class="pill small pull-right"
					style="background-color: var(--bg-${status_color[node.data.status]}); color: var(--text-on-${
						status_color[node.data.status]
					}); font-weight:500">
					${node.data.status}
				</span>
			`).insertBefore(node.$ul);
		}
	},
	breadcrumb: "Performance",
	get_tree_root: false,
	add_tree_node: "hrms.hr.doctype.goal.goal.add_tree_node",
	root_label: __("All Goals"),
	ignore_fields: ["parent_goal"],
	post_render(treeview) {
		frappe.treeview_settings["Goal"].treeview = {};
		$.extend(frappe.treeview_settings["Goal"].treeview, treeview);
	},
	get_label(node) {
		if (node.title && node.title !== node.label) {
			return (
				__(node.title) + ` <span class="text-muted">(${node.data.employee_name})</span>`
			);
		} else {
			return __(node.title || node.label);
		}
	},
	toolbar: [
		{
			label: __("Update Progress"),
			condition: function (node) {
				return !node.root && !node.expandable;
			},
			click: function (node) {
				const dialog = new frappe.ui.Dialog({
					title: __("Update Progress"),
					fields: [
						{
							fieldname: "progress",
							fieldtype: "Percent",
							in_place_edit: true,
							default: node.data.progress,
						},
					],
					primary_action: function () {
						dialog.hide();
						return update_progress(node, dialog.get_values()["progress"]);
					},
					primary_action_label: __("Update"),
				});
				dialog.show();
			},
		},
		{
			label: __("Mark as Completed"),
			condition: function (node) {
				return !node.is_root && !node.expandable && node.data.status != "Completed";
			},
			click: function (node) {
				frappe.confirm(__("Mark {0} as Completed?", [node.label.bold()]), () =>
					update_progress(node, 100),
				);
			},
		},
	],
	extend_toolbar: true,
};

function update_progress(node, progress) {
	return frappe
		.call({
			method: "hrms.hr.doctype.goal.goal.update_progress",
			args: {
				goal: node.data.value,
				progress: progress,
			},
		})
		.then((r) => {
			if (!r.exc && r.message) {
				frappe.treeview_settings["Goal"].treeview.tree.load_children(
					frappe.treeview_settings["Goal"].treeview.tree.root_node,
					true,
				);

				frappe.show_alert({
					message: __("Goal updated successfully"),
					indicator: "green",
				});
			} else {
				frappe.msgprint(__("Could not update Goal"));
			}
		});
}
