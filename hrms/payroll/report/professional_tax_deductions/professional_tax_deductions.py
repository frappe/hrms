# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.query_builder import DocType

from hrms.payroll.report.provident_fund_deductions.provident_fund_deductions import get_conditions


def execute(filters=None):
	data = get_data(filters)
	columns = get_columns(filters) if len(data) else []

	return columns, data


def get_columns(filters):
	columns = [
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 200,
		},
		{
			"label": _("Employee Name"),
			"fieldname": "employee_name",
			"width": 160,
		},
		{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 140},
	]

	return columns


def get_data(filters):
	data = []
	SalarySlip = DocType("Salary Slip")
	SalaryDetail = DocType("Salary Detail")
	SalaryComponent = DocType("Salary Component")

	component_type_list = (
		frappe.qb.from_(SalaryComponent)
		.select(SalaryComponent.name, SalaryComponent.component_type)
		.where(SalaryComponent.component_type == "Professional Tax")
		.run(pluck="name")
	)

	if not len(component_type_list):
		return []

	filter_clauses = get_conditions(filters)
	base_where = SalarySlip.docstatus == 1
	for clause in filter_clauses:
		base_where = base_where & clause

	entry = (
		frappe.qb.from_(SalarySlip)
		.join(SalaryDetail)
		.on(SalarySlip.name == SalaryDetail.parent)
		.select(
			SalarySlip.employee,
			SalarySlip.employee_name,
			SalaryDetail.salary_component,
			SalaryDetail.amount,
		)
		.where(
			(SalaryDetail.parentfield == "deductions")
			& (SalaryDetail.parenttype == "Salary Slip")
			& (SalaryDetail.salary_component.isin(component_type_list))
			& base_where
		)
		.run(as_dict=True)
	)

	for d in entry:
		employee = {"employee": d.employee, "employee_name": d.employee_name, "amount": d.amount}

		data.append(employee)

	return data
