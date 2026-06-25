frappe.provide("frappe.treeview_settings");

frappe.treeview_settings["Position"] = {
	get_tree_nodes: "hrms.organization_structure.doctype.position.position.get_children",
	add_tree_node: "hrms.organization_structure.doctype.position.position.add_tree_node",
	filters: [
		{
			fieldname: "organization_unit",
			fieldtype: "Link",
			options: "Organization Unit",
			label: __("Organization Unit"),
		},
		{
			fieldname: "location_1",
			fieldtype: "Select",
			options: ["", "Head Office", "District Office", "Branch"],
			label: __("Location 1"),
		},
		{
			fieldname: "site_organization_unit",
			fieldtype: "Link",
			options: "Organization Unit",
			label: __("Site Organization Unit"),
		},
		{
			fieldname: "job_grade",
			fieldtype: "Link",
			options: "Job Grade",
			label: __("Job Grade"),
		},
		{
			fieldname: "position_status",
			fieldtype: "Select",
			options: ["", "Active", "Inactive"],
			label: __("Position Status"),
		},
	],
	fields: [
		{
			fieldtype: "Data",
			fieldname: "position_name",
			label: __("Position Name"),
		},
		{
			fieldtype: "Link",
			fieldname: "position_template",
			label: __("Position Template"),
			options: "Position Template",
		},
		{
			fieldtype: "Link",
			fieldname: "organization_unit",
			label: __("Organization Unit"),
			options: "Organization Unit",
		},
		{
			fieldtype: "Link",
			fieldname: "site_organization_unit",
			label: __("Site Organization Unit"),
			options: "Organization Unit",
		},
	],
	ignore_fields: ["parent_position"],
	root_label: "All Positions",
	get_tree_root: true,
	onrender(node) {
		if (!node.data) return;

		const indicator = node.data.is_occupied ? "green" : "orange";
		const label = node.data.is_occupied
			? node.data.current_employee || __("Occupied")
			: __("Vacant");

		$(`
			<span class="pill small pull-right" style="background-color: var(--bg-${indicator}); color: var(--text-on-${indicator}); font-weight:500;">
				${label}
			</span>
		`).insertBefore(node.$ul);
	},
	breadcrumb: "Organization Structure",
};
