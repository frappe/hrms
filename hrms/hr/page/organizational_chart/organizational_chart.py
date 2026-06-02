import frappe
from frappe import _
from frappe.query_builder.functions import Count


@frappe.whitelist()
def get_children(parent: str | None = None, company: str | None = None, exclude_node: str | None = None):
	filters = [["status", "=", "Active"]]
	if company and not is_all_companies(company):
		filters.append(["company", "=", company])

	if parent and company and parent != company:
		filters.append(["reports_to", "=", parent])
	else:
		filters.append(["reports_to", "=", ""])

	if exclude_node:
		filters.append(["name", "!=", exclude_node])

	employees = frappe.get_all(
		"Employee",
		fields=[
			"employee_name as name",
			"name as id",
			"lft",
			"rgt",
			"reports_to",
			"image",
			"designation as title",
		],
		filters=filters,
		order_by="name",
	)

	for employee in employees:
		employee.connections = get_connections(employee.id, employee.lft, employee.rgt, company)
		employee.expandable = bool(employee.connections)

	return employees


def is_all_companies(company: str | None) -> bool:
	return company in ("All Companies", _("All Companies"))


def get_connections(employee: str, lft: int, rgt: int, company: str | None = None) -> int:
	Employee = frappe.qb.DocType("Employee")
	query = (
		frappe.qb.from_(Employee)
		.select(Count(Employee.name))
		.where((Employee.lft > lft) & (Employee.rgt < rgt) & (Employee.status == "Active"))
	)

	if company and not is_all_companies(company):
		query = query.where(Employee.company == company)

	query = query.run()

	return query[0][0]
