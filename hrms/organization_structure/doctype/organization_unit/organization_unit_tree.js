frappe.provide("frappe.treeview_settings");

frappe.treeview_settings["Organization Unit"] = {
	get_tree_nodes:
		"hrms.organization_structure.doctype.organization_unit.organization_unit.get_children",
	add_tree_node:
		"hrms.organization_structure.doctype.organization_unit.organization_unit.add_tree_node",
	filters: [
		{
			fieldname: "unit_type",
			fieldtype: "Select",
			options: [
				"",
				"Executive",
				"Function",
				"Process",
				"Sub-Process",
				"Department",
				"District",
				"Team",
				"Branch",
				"Sub-Team",
				"Other",
			],
			label: __("Unit Type"),
		},
		{
			fieldname: "status",
			fieldtype: "Select",
			options: ["", "Active", "Inactive"],
			label: __("Status"),
		},
	],
	fields: [
		{
			fieldtype: "Data",
			fieldname: "unit_name",
			label: __("Unit Name"),
			reqd: 1,
		},
		{
			fieldtype: "Data",
			fieldname: "unit_code",
			label: __("Unit Code"),
		},
		{
			fieldtype: "Select",
			fieldname: "unit_type",
			label: __("Unit Type"),
			options: [
				"",
				"Executive",
				"Function",
				"Process",
				"Sub-Process",
				"Department",
				"District",
				"Team",
				"Branch",
				"Sub-Team",
				"Other",
			],
		},
		{
			fieldtype: "Check",
			fieldname: "is_group",
			label: __("Is Group"),
			description: __("Child units can only be created under a 'Group' unit."),
		},
	],
	ignore_fields: ["parent_organization_unit"],
	root_label: "All Organization Units",
	get_tree_root: true,
	menu_items: [
		{
			label: __("New Organization Unit"),
			action: function () {
				frappe.new_doc("Organization Unit", true);
			},
			condition: 'frappe.boot.user.can_create.indexOf("Organization Unit") !== -1',
		},
	],
	onrender(node) {
		if (node.data && node.data.unit_type) {
			$(`
				<span class="pill small pull-right" style="background-color: var(--bg-light-gray); color: var(--text-on-gray);">
					${node.data.unit_type}
				</span>
			`).insertBefore(node.$ul);
		}
	},
	breadcrumb: "Organization Structure",
};
