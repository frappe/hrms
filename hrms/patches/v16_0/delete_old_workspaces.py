import frappe


def execute():
	old_workspaces = ["Expense Claims", "Salary Payout", "Employee Lifecycle", "Overview", "Attendance", "HR"]

	for workspace in old_workspaces:
		icon_link_types = []

		if workspace_doc := frappe.db.get_value(
			"Workspace", workspace, ["name", "public", "for_user"], as_dict=True
		):
			if workspace_doc.public and not workspace_doc.for_user:
				frappe.delete_doc("Workspace", workspace, force=True)
				icon_link_types.append("Workspace")
		else:
			icon_link_types.append("Workspace")

		if sidebar := frappe.db.get_value("Workspace Sidebar", workspace, ["name", "for_user"], as_dict=True):
			if not sidebar.for_user:
				frappe.delete_doc("Workspace Sidebar", sidebar.name)
				icon_link_types.append("Workspace Sidebar")
		else:
			icon_link_types.append("Workspace Sidebar")

		if icon_link_types:
			old_icons = frappe.get_all(
				"Desktop Icon",
				filters={"link_to": workspace, "link_type": ["in", icon_link_types]},
				pluck="name",
			)
			for icon in old_icons:
				frappe.delete_doc("Desktop Icon", icon)
