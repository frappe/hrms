# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe


import frappe
from frappe import _
from frappe.utils import date_diff, getdate, today


def execute(filters=None):
	validate_date(filters)
	columns = get_columns(filters)
	data = get_data(filters)
	processed_data = process_data(data, filters)
	return columns, processed_data


def validate_date(filters):
	if date_diff(filters.get("to_date"), filters.get("from_date")) < 0:
		frappe.throw(_("To Date cannot be before From Date."))


def get_data(filters):
	emp = frappe.qb.DocType("Employee")
	query = (
		frappe.qb.from_(emp)
		.select(
			emp.name.as_("employee"),
			emp.employee_name,
			emp.date_of_joining,
			emp.department,
			emp.designation,
			emp.gender,
			emp.company,
		)
		.where(emp.status == "Active")
		.orderby(emp.date_of_joining)
	)

	if filters.get("company"):
		query = query.where(emp.company == filters.get("company"))

	return query.run(as_dict=True)


def process_data(data, filters):
	processed_data = []
	for emp in data:
		doj = emp.date_of_joining
		year = getdate(filters.get("from_date")).year

		try:
			anniversary = doj.replace(year=year)
		except ValueError:
			anniversary = getdate(f"{year}-02-28")

		if getdate(filters.get("from_date")) <= anniversary <= getdate(filters.get("to_date")):
			years = round(date_diff(today(), emp.date_of_joining) / 365)
			emp.update({"service_years": years})
			processed_data.append(emp)

	return processed_data


def get_columns(filters):
	columns = [
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 170,
		},
		{
			"label": _("Employee Name"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 170,
		},
		{
			"label": _("Gender"),
			"fieldname": "gender",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Joining Date"),
			"fieldname": "date_of_joining",
			"fieldtype": "Date",
			"width": 120,
		},
		{
			"label": _("Service Years"),
			"fieldname": "service_years",
			"fieldtype": "Int",
			"precision": "2",
			"width": 100,
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 170,
		},
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 170,
		},
		{
			"label": _("Designation"),
			"fieldname": "designation",
			"fieldtype": "Link",
			"options": "Designation",
			"width": 170,
		},
	]
	return columns
