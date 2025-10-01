# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.utils import getdate


def execute(filters: dict | None = None):
	columns = get_columns()
	data = get_data(filters)

	return columns, data


def get_columns() -> list[dict]:
	return [
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120,
		},
		{
			"label": _("Employee Name"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Salary Component"),
			"fieldname": "salary_component",
			"fieldtype": "Link",
			"options": "Salary Component",
			"width": 150,
		},
		{
			"label": _("Yearly Benefit"),
			"fieldname": "yearly_benefit",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Total Accrued"),
			"fieldname": "total_accrued",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Total Payout"),
			"fieldname": "total_payout",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Unpaid Accrual"),
			"fieldname": "unpaid_accrual",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Flexible Component"),
			"fieldname": "flexible_benefit",
			"fieldtype": "Check",
			"width": 120,
		},
		{
			"label": _("Action"),
			"fieldname": "create_additional_salary",
			"fieldtype": "Data",
			"width": 150,
		},
	]


def get_data(filters):
	EBL = DocType("Employee Benefit Ledger")
	EMP = DocType("Employee")
	SC = DocType("Salary Component")

	query = (
		frappe.qb.from_(EBL)
		.inner_join(EMP)
		.on(EBL.employee == EMP.name)
		.inner_join(SC)
		.on(EBL.salary_component == SC.name)
		.select(
			EBL.employee,
			EBL.employee_name,
			EBL.payroll_period,
			EBL.salary_component,
			EBL.transaction_type,
			EBL.amount,
			EBL.yearly_benefit,
			SC.accrual_component,
			EBL.flexible_benefit,
		)
	)

	if filters.get("company"):
		query = query.where(EBL.company == filters["company"])

	if filters.get("employee"):
		query = query.where(EBL.employee == filters["employee"])

	if filters.get("department"):
		query = query.where(EMP.department == filters["department"])

	if filters.get("branch"):
		query = query.where(EMP.branch == filters["branch"])

	if filters.get("payroll_period"):
		query = query.where(EBL.payroll_period == filters["payroll_period"])

	if filters.get("salary_component"):
		query = query.where(EBL.salary_component == filters["salary_component"])

	# Always filter accrual_component
	query = query.where(SC.accrual_component == 1)

	flexible_benefit = filters.get("flexible_benefit")
	if flexible_benefit == "Yes":
		query = query.where(EBL.flexible_benefit == 1)
	elif flexible_benefit == "No":
		query = query.where((EBL.flexible_benefit == 0) | (EBL.flexible_benefit.isnull()))

	query = query.orderby(EBL.employee, EBL.salary_component, EBL.flexible_benefit)
	ledger_entries = query.run(as_dict=True)

	# group data by employee, salary_component, and flexible_benefit
	grouped_data = {}

	for entry in ledger_entries:
		key = (
			entry.employee,
			entry.employee_name,
			entry.payroll_period,
			entry.salary_component,
			entry.flexible_benefit or 0,
		)

		if key not in grouped_data:
			grouped_data[key] = {
				"employee": entry.employee,
				"employee_name": entry.employee_name,
				"payroll_period": entry.payroll_period,
				"salary_component": entry.salary_component,
				"flexible_benefit": entry.flexible_benefit or 0,
				"yearly_benefit": entry.yearly_benefit or 0,
				"total_accrued": 0,
				"total_payout": 0,
				"unpaid_accrual": 0,
			}

		if entry.transaction_type == "Accrual":
			grouped_data[key]["total_accrued"] += entry.amount or 0
		elif entry.transaction_type == "Payout":
			grouped_data[key]["total_payout"] += entry.amount or 0

	# Calculate unpaid accrual and prepare final data
	data = []
	for row_data in grouped_data.values():
		row_data["unpaid_accrual"] = row_data["total_accrued"] - row_data["total_payout"]

		# Add create additional salary button only for non-flexible benefits with unpaid accrual
		if not row_data["flexible_benefit"] and row_data["unpaid_accrual"] > 0:
			row_data["create_additional_salary"] = f"""
				<a
						onclick="create_additional_salary('{row_data['employee']}',
													   '{row_data['salary_component']}',
													   {row_data['unpaid_accrual']})">
					Create Additional Salary
				</a>
			"""
		else:
			row_data["create_additional_salary"] = ""

		data.append(row_data)
	return data
