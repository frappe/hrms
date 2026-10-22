import frappe
from frappe.query_builder.functions import Count
from frappe.utils import nowdate


@frappe.whitelist()
def get_children(parent: str | None = None, company: str | None = None, exclude_node: str | None = None):
	filters = [["status", "=", "Active"]]
	if company and company != "All Companies":
		filters.append(["company", "=", company])

	if parent and company and parent != company:
		filters.append(["reports_to", "=", parent])
	else:
		filters.append(["reports_to", "=", ""])

	if exclude_node:
		filters.append(["name", "!=", exclude_node])

	employees = frappe.get_list(
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
		employee.connections = get_connections(employee.id, employee.lft, employee.rgt)
		employee.expandable = bool(employee.connections)

	return employees


def get_connections(employee: str, lft: int, rgt: int) -> int:
	Employee = frappe.qb.DocType("Employee")
	query = (
		frappe.qb.from_(Employee)
		.select(Count(Employee.name))
		.where((Employee.lft > lft) & (Employee.rgt < rgt) & (Employee.status == "Active"))
	).run()

	return query[0][0]


PEOPLE_FIELDS = [
	"name",
	"employee_name",
	"designation",
	"department",
	"branch",
	"company",
	"image",
	"user_id",
	"company_email",
	"reports_to",
	"date_of_birth",
	"date_of_joining",
]


@frappe.whitelist(methods=["GET"])
def get_people():
	"""Every Active employee the user can read, for the org chart and the directory."""
	frappe.has_permission("Employee", "read", throw=True)

	people = frappe.get_list(
		"Employee",
		fields=PEOPLE_FIELDS,
		filters={"status": "Active"},
		order_by="employee_name asc",
		limit_page_length=0,
	)

	today = nowdate()
	leaves = {
		leave.employee: leave
		for leave in frappe.get_all(
			"Leave Application",
			fields=["employee", "half_day", "to_date"],
			filters={
				"docstatus": 1,
				"status": "Approved",
				"from_date": ["<=", today],
				"to_date": [">=", today],
			},
			limit_page_length=0,
		)
	}

	department_names = dict(
		frappe.get_all("Department", fields=["name", "department_name"], as_list=True, limit_page_length=0)
	)

	reports = {}
	for person in people:
		if person.reports_to:
			reports[person.reports_to] = reports.get(person.reports_to, 0) + 1

	for person in people:
		leave = leaves.get(person.name)
		person.department_name = department_names.get(person.department) or ""
		person.on_leave_today = 1 if leave else 0
		person.leave_half_day = leave.half_day if leave else 0
		person.leave_to_date = leave.to_date if leave else None
		person.reports = reports.get(person.name, 0)

	return people
