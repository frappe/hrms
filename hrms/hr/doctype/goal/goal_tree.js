frappe.provide("frappe.treeview_settings");

frappe.treeview_settings["Goal"] = {
	get_tree_nodes: "hrms.hr.doctype.goal.goal.get_children",
	filters: [
		{
			fieldname: "company",
			fieldtype:"Select",
			options: erpnext.utils.get_tree_options("company"),
			label: __("Company"),
			default: erpnext.utils.get_tree_default("company")
		},
		{
			fieldname: "employee",
			fieldtype:"Link",
			options: "Employee",
			label: __("Employee")
		},
		{
			fieldname: "goal",
			fieldtype:"Link",
			options: "Goal",
			label: __("Goal"),
			get_query: function() {
				const me = frappe.treeview_settings["Goal"];
				var appraisal_cycle = me.page.fields_dict.appraisal_cycle.get_value();
				var args = [["Goal", "is_group", "=", 1]];
				if (project) {
					args.push(["Goal", "Appraisal Cycle", "=", appraisal_cycle]);
				}
				return {
					filters: args
				};
			}
		},
	],
	fields: [
		{
			fieldtype: 'Data',
			fieldname: 'goal_name',
			label: __('Goal'),
			reqd: 1
		},
		{
			fieldtype: 'Check',
			fieldname: 'is_group',
			label: __('Is Group'),
			description: __("Child nodes can only be created under 'Group' type nodes")
		},
		{
			fieldtype: 'Link',
			fieldname: 'employee',
			label: __('Employee'),
			options: 'Employee'
		},
		{
			fieldtype: 'Link',
			fieldname: 'appraisal_cycle',
			label: __('Appraisal Cycle'),
			options: 'Appraisal Cycle'
		},
		{
			fieldtype: 'Date',
			fieldname: 'start_date',
			label: __('Start Date'),
			reqd: 1
		},
		{
			fieldtype: 'Date',
			fieldname: 'due_date',
			label: __('Due Date'),
		},
		{
			fieldtype: 'Percent',
			fieldname: 'progress',
			label: __('Progress'),
		},
		{
			fieldtype: 'Select',
			options: ["Low", "Medium", "High"],
			fieldname: 'priority',
			label: __('Priority'),
		},
		{
			fieldtype: 'Link',
			fieldname: 'company',
			label: __('Company'),
			options: 'Company',
			default: () => {
				return cur_page.page.page.fields_dict.company.value;
			},
			hidden: 1
		}
	],
	onrender: function (node) {
		if (node.data.completion_count !== undefined) {
			$(`
				<span class='balance-area pull-right text-muted small'>
				${node.data.completion_count}
				</span>
			`).insertBefore(node.$ul);
		}
		else if (node.data && node.data.status !== undefined) {
			const status_color = {
				'Pending': 'yellow',
				'In Progress': 'orange',
				'Completed': 'green',
				'Archived': 'gray',
			};
			$(`
				<span
					class="pill small pull-right"
					style="background-color: var(--bg-${status_color[node.data.status]}); color: var(--text-on-${status_color[node.data.status]}); font-weight:500">
					${node.data.status}
				</span>
			`).insertBefore(node.$ul);
		}
	},
	breadcrumb: "Performance",
	get_tree_root: false,
	root_label: "All Goals",
	ignore_fields: ["parent_goal"],
	onload: function(treeview) {
		// frappe.treeview_settings["Goal"].treeview = {};
		// $.extend(frappe.treeview_settings["Goal"].treeview, treeview);

		// if (!me.args["employee"]) {
		// 	frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name", (r) => {
		// 		me.args["employee"] = r.name;
		// 	});
		// }
		me.make_tree();
	},
	post_render: function (treeview) {
		frappe.treeview_settings['Goal'].treeview = {};
		$.extend(frappe.treeview_settings['Goal'].treeview, treeview);
	},
	get_label: function(node) {
		if (node.title && node.title !== node.label) {
			return __(node.title) + ` <span class='text-muted'>(${node.data.employee_name})</span>`;
		} else {
			return __(node.title || node.label);
		}
	},
	toolbar: [
		{
			label:__("Update Progress"),
			condition: function(node) {
				return !node.root && !node.expandable;
			},
			click: function(node) {
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
					primary_action: function() {
						dialog.hide();
						return frappe.call({
							method: "hrms.hr.doctype.goal.goal.update_progress",
							args: {
								progress: dialog.get_values()["progress"],
								goal: node.data.value
							},
							callback: function(r) {
								if (!r.exc && r.message) {
									frappe.treeview_settings['Goal'].treeview.tree.load_children(node.parent_node, true);

									frappe.show_alert({
										message: __('Progress Updated'),
										indicator: 'green'
									});
								} else {
									frappe.msgprint(__('Could not update progress'));
								}
							}
						});
					},
					primary_action_label: __('Update')
				});
				dialog.show();
			}
		}
	],
	extend_toolbar: true
};
