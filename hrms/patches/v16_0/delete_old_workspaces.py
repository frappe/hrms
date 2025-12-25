import frappe


def execute():
	old_workspaces = [
		"Expense Claims",
		"Salary Payout",
		"Employee Lifecycle",
		"Overview",
		"Attendance",
	]

	for workspace in old_workspaces:
		if frappe.db.exists("Workspace", {"name": workspace, "public": 1, "for_user": ("is", "Not Set")}):
			frappe.delete_doc("Workspace", workspace, force=True)
		if sidebar := frappe.db.exists(
			"Workspace Sidebar", {"name": workspace, "for_user": ("is", "Not Set")}
		):
			frappe.delete_doc("Workspace Sidebar", sidebar)
		if icon := frappe.db.exists("Desktop Icon", {"link_type": "Workspace", "link_to": workspace}):
			frappe.delete_doc("Desktop Icon", icon)
