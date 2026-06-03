# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.query_builder.functions import Extract

import erpnext


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data


def get_columns(filters):
	columns = [
		{
			"label": _("Branch"),
			"options": "Branch",
			"fieldname": "branch",
			"fieldtype": "Link",
			"width": 200,
		},
		{
			"label": _("Employee Name"),
			"options": "Employee",
			"fieldname": "employee_name",
			"fieldtype": "Link",
			"width": 160,
		},
		{
			"label": _("Employee"),
			"options": "Employee",
			"fieldname": "employee",
			"fieldtype": "Link",
			"width": 140,
		},
		{
			"label": _("Gross Pay"),
			"fieldname": "gross_pay",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 140,
		},
		{
			"label": _("Net Pay"),
			"fieldname": "net_pay",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 140,
		},
		{"label": _("Bank"), "fieldname": "bank", "fieldtype": "Data", "width": 140},
		{"label": _("Account No"), "fieldname": "account_no", "fieldtype": "Data", "width": 140},
	]
	if erpnext.get_region() == "India":
		columns += [
			{"label": _("IFSC"), "fieldname": "ifsc", "fieldtype": "Data", "width": 140},
			{"label": _("MICR"), "fieldname": "micr", "fieldtype": "Data", "width": 140},
		]

	return columns


def get_conditions(filters):
	SalarySlip = DocType("Salary Slip")
	filter_clauses = []

	if filters.get("department"):
		filter_clauses.append(SalarySlip.department == filters["department"])
	if filters.get("branch"):
		filter_clauses.append(SalarySlip.branch == filters["branch"])
	if filters.get("company"):
		filter_clauses.append(SalarySlip.company == filters["company"])
	if filters.get("month"):
		filter_clauses.append(Extract("month", SalarySlip.start_date) == int(filters["month"]))
	if filters.get("year"):
		filter_clauses.append(Extract("year", SalarySlip.start_date) == int(filters["year"]))

	return filter_clauses


def get_data(filters):
	SalarySlip = DocType("Salary Slip")
	filter_clauses = get_conditions(filters)

	fields = ["employee", "branch", "bank_name", "bank_ac_no", "salary_mode"]
	if erpnext.get_region() == "India":
		fields += ["ifsc_code", "micr_code"]

	employee_details = frappe.get_list("Employee", fields=fields)
	employee_data_dict = {}

	for d in employee_details:
		employee_data_dict.setdefault(
			d.employee,
			{
				"bank_ac_no": d.bank_ac_no,
				"ifsc_code": d.ifsc_code or None,
				"micr_code": d.micr_code or None,
				"branch": d.branch,
				"salary_mode": d.salary_mode,
				"bank_name": d.bank_name,
			},
		)

	base_where = SalarySlip.docstatus == 1
	for clause in filter_clauses:
		base_where = base_where & clause

	entry = (
		frappe.qb.from_(SalarySlip)
		.select(SalarySlip.employee, SalarySlip.employee_name, SalarySlip.gross_pay, SalarySlip.net_pay)
		.where(base_where)
		.run(as_dict=True)
	)

	data = []

	for d in entry:
		employee = {
			"branch": employee_data_dict.get(d.employee).get("branch"),
			"employee_name": d.employee_name,
			"employee": d.employee,
			"gross_pay": d.gross_pay,
			"net_pay": d.net_pay,
		}

		if employee_data_dict.get(d.employee).get("salary_mode") == "Bank":
			employee["bank"] = employee_data_dict.get(d.employee).get("bank_name")
			employee["account_no"] = employee_data_dict.get(d.employee).get("bank_ac_no")
			if erpnext.get_region() == "India":
				employee["ifsc"] = employee_data_dict.get(d.employee).get("ifsc_code")
				employee["micr"] = employee_data_dict.get(d.employee).get("micr_code")
		else:
			employee["account_no"] = employee_data_dict.get(d.employee).get("salary_mode")

		if filters.get("type") and employee_data_dict.get(d.employee).get("salary_mode") == filters.get(
			"type"
		):
			data.append(employee)
		elif not filters.get("type"):
			data.append(employee)

	return data
