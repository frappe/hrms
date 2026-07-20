# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from copy import deepcopy

import frappe
from frappe import _
from frappe.query_builder import Criterion
from frappe.query_builder.functions import Count

from erpnext.accounts.utils import build_qb_match_conditions


def execute(filters=None):
	if not filters:
		filters = {}

	if not filters["company"]:
		frappe.throw(_("{0} is mandatory").format(_("Company")))

	columns = get_columns()
	companies = get_companies(filters.get("company"))
	employees = get_employees(filters, companies)
	parameters = get_parameters(filters)

	chart = get_chart_data(parameters, filters, companies)
	return columns, employees, None, chart


def get_columns():
	return [
		_("Employee") + ":Link/Employee:120",
		_("Name") + ":Data:200",
		_("Date of Birth") + ":Date:100",
		_("Branch") + ":Link/Branch:120",
		_("Department") + ":Link/Department:120",
		_("Designation") + ":Link/Designation:120",
		_("Gender") + "::100",
		_("Company") + ":Link/Company:120",
	]


def get_companies(company):
	child_companies = frappe.get_all("Company", filters={"parent_company": company}, pluck="name")
	if child_companies:
		return [company, *child_companies]
	return [company]


def get_employees(filters, companies):
	filters_for_employees = frappe._dict(deepcopy(filters) or {})
	filters_for_employees["status"] = "Active"
	filters_for_employees[filters.get("parameter").lower().replace(" ", "_")] = ["is", "set"]
	filters_for_employees.pop("parameter")
	if len(companies) > 1:
		filters_for_employees["company"] = ["in", companies]
	return frappe.get_list(
		"Employee",
		filters=filters_for_employees,
		fields=[
			"name",
			"employee_name",
			"date_of_birth",
			"branch",
			"department",
			"designation",
			"gender",
			"company",
		],
		as_list=True,
	)


def get_parameters(filters):
	if filters.get("parameter") == "Grade":
		parameter = "Employee Grade"
	else:
		parameter = filters.get("parameter")
	return frappe.get_all(parameter, pluck="name")


def get_chart_data(parameters, filters, companies):
	if not parameters:
		parameters = []
	datasets = []
	parameter_field_name = filters.get("parameter").lower().replace(" ", "_")
	label = []
	employee = frappe.qb.DocType("Employee")
	for parameter in parameters:
		if parameter:
			query = (
				frappe.qb.from_(employee)
				.select(Count(employee.name).as_("count"))
				.where(employee.status == "Active")
				.where(employee[parameter_field_name] == parameter)
				.where(Criterion.all(build_qb_match_conditions("Employee")))
			)
			if len(companies) > 1:
				query = query.where(employee.company.isin(companies))
			else:
				query = query.where(employee.company == companies[0])
			total_employee = query.run()
			if total_employee[0][0]:
				label.append(parameter)
			datasets.append(total_employee[0][0])

	values = [value for value in datasets if value != 0]

	if len(companies) > 1:
		total_employee = frappe.db.count("Employee", {"status": "Active", "company": ["in", companies]})
	else:
		total_employee = frappe.db.count("Employee", {"status": "Active", "company": companies[0]})
	others = total_employee - sum(values)

	label.append("Not Set")
	values.append(others)
	chart = {"data": {"labels": label, "datasets": [{"name": "Employees", "values": values}]}}
	chart["type"] = "donut"
	return chart
