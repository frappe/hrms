import frappe


def execute():
	old_workspaces = ["Expense Claims", "Salary Payout", "Employee Lifecycle", "Overview", "Attendance", "HR"]

	for workspace in old_workspaces:
		if workspace_doc := frappe.db.get_value(
			"Workspace", workspace, ["name", "public", "for_user"], as_dict=True
		):
			if workspace_doc.public and not workspace_doc.for_user:
				frappe.delete_doc("Workspace", workspace, force=True)

		if sidebar := frappe.db.get_value("Workspace Sidebar", workspace, ["name", "for_user"], as_dict=True):
			if not sidebar.for_user:
				frappe.delete_doc("Workspace Sidebar", sidebar.name)

		old_icons = frappe.get_all(
			"Desktop Icon",
			filters={"link_to": workspace, "link_type": ["in", ["Workspace", "Workspace Sidebar"]]},
			pluck="name",
		)
		for icon in old_icons:
			frappe.delete_doc("Desktop Icon", icon)
