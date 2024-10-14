# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.query_builder.functions import Extract

import erpnext

Filters = frappe._dict


def execute(filters: Filters = None) -> tuple:
	is_indian_company = erpnext.get_region(filters.get("company")) == "India"
	columns = get_columns(is_indian_company)
	data = get_data(filters, is_indian_company)

	return columns, data


def get_columns(is_indian_company: bool) -> list[dict]:
	columns = [
		{
			"label": _("Employee"),
			"options": "Employee",
			"fieldname": "employee",
			"fieldtype": "Link",
			"width": 200,
		},
		{
			"label": _("Employee Name"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 160,
		},
	]

	if is_indian_company:
		columns.append(
			{"label": _("PAN Number"), "fieldname": "pan_number", "fieldtype": "Data", "width": 140}
		)

	columns += [
		{"label": _("Income Tax Component"), "fieldname": "it_comp", "fieldtype": "Data", "width": 170},
		{
			"label": _("Income Tax Amount"),
			"fieldname": "it_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 140,
		},
		{
			"label": _("Gross Pay"),
			"fieldname": "gross_pay",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 140,
		},
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 140},
	]

	return columns


def get_data(filters: Filters, is_indian_company: bool) -> list[dict]:
	data = []

	employee_pan_dict = {}
	if is_indian_company:
		employee_pan_dict = frappe._dict(
			frappe.get_all("Employee", fields=["name", "pan_number"], as_list=True)
		)

	deductions = get_income_tax_deductions(filters)

	for d in deductions:
		employee = {
			"employee": d.employee,
			"employee_name": d.employee_name,
			"it_comp": d.salary_component,
			"posting_date": d.posting_date,
			"it_amount": d.amount,
			"gross_pay": d.gross_pay,
		}

		if is_indian_company:
			employee["pan_number"] = employee_pan_dict.get(d.employee)

		data.append(employee)

	return data


def get_income_tax_deductions(filters: Filters) -> list[dict]:
	component_types = frappe.get_all("Salary Component", filters={"is_income_tax_component": 1}, pluck="name")
	if not component_types:
		return []

	SalarySlip = frappe.qb.DocType("Salary Slip")
	SalaryDetail = frappe.qb.DocType("Salary Detail")

	query = (
		frappe.qb.from_(SalarySlip)
		.inner_join(SalaryDetail)
		.on(SalarySlip.name == SalaryDetail.parent)
		.select(
			SalarySlip.employee,
			SalarySlip.employee_name,
			SalarySlip.posting_date,
			SalaryDetail.salary_component,
			SalaryDetail.amount,
			SalarySlip.gross_pay,
		)
		.where(
			(SalarySlip.docstatus == 1)
			& (SalaryDetail.parentfield == "deductions")
			& (SalaryDetail.parenttype == "Salary Slip")
			& (SalaryDetail.salary_component.isin(component_types))
		)
	)

	for field in ["department", "branch", "company"]:
		if filters.get(field):
			query = query.where(getattr(SalarySlip, field) == filters.get(field))

	if filters.get("month"):
		query = query.where(Extract("month", SalarySlip.start_date) == filters.month)

	if filters.get("year"):
		query = query.where(Extract("year", SalarySlip.start_date) == filters.year)

	return query.run(as_dict=True)
