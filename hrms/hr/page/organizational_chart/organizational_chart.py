import frappe
from frappe import _


@frappe.whitelist()
def get_children(parent: str | None = None, company: str | None = None, exclude_node: str | None = None):
	if not frappe.get_doc("Page", "organizational-chart").is_permitted():
		frappe.throw(_("Not Permitted"), frappe.PermissionError)

	filters = [["status", "=", "Active"]]
	if company and company != "All Companies":
		frappe.has_permission("Company", "read", company, throw=True)
		filters.append(["company", "=", company])

	if parent and company and parent != company:
		parent_bounds = frappe.db.get_value("Employee", parent, ["lft", "rgt"], as_dict=True)
		if not parent_bounds:
			return []
		filters.extend([["lft", ">", parent_bounds.lft], ["rgt", "<", parent_bounds.rgt]])

	employees = frappe.get_all(
		"Employee",
		fields=[
			"employee_name as name",
			"name as id",
			"lft",
			"rgt",
			"image",
			"designation as title",
			"department",
		],
		filters=filters,
		order_by="lft",
	)

	nodes = []
	for employee in employees:
		if nodes and employee.lft < nodes[-1].rgt:
			nodes[-1].connections += 1
		else:
			employee.connections = 0
			nodes.append(employee)

	for node in nodes:
		node.expandable = bool(node.connections)
		node.pop("lft")
		node.pop("rgt")

	return sorted((node for node in nodes if node.id != exclude_node), key=lambda node: node.id)
