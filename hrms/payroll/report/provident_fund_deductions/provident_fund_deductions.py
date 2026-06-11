# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.query_builder.functions import Extract
from frappe.utils import getdate


def execute(filters=None):
	data = []
	provident_fund_components = ["Provident Fund", "Additional Provident Fund", "Provident Fund Loan"]
	if not frappe.db.exists("Salary Component", {"component_type": ["in", provident_fund_components]}):
		frappe.msgprint(
			_(
				"Salary components of type Provident Fund, Additional Provident Fund or Provident Fund Loan are not set up."
			),
			title=_("Missing Salary Components"),
			indicator="red",
		)
	else:
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
		{"label": _("PF Account"), "fieldname": "pf_account", "fieldtype": "Data", "width": 140},
		{"label": _("PF Amount"), "fieldname": "pf_amount", "fieldtype": "Currency", "width": 140},
		{
			"label": _("Additional PF"),
			"fieldname": "additional_pf",
			"fieldtype": "Currency",
			"width": 140,
		},
		{"label": _("PF Loan"), "fieldname": "pf_loan", "fieldtype": "Currency", "width": 140},
		{"label": _("Total"), "fieldname": "total", "fieldtype": "Currency", "width": 140},
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
	if filters.get("mode_of_payment"):
		filter_clauses.append(SalarySlip.mode_of_payment == filters["mode_of_payment"])

	return filter_clauses


def prepare_data(entry, component_type_dict):
	data_list = {}
	Employee = DocType("Employee")

	employee_account_dict = frappe._dict(
		frappe.qb.from_(Employee).select(Employee.name, Employee.provident_fund_account).run()
	)

	for d in entry:
		component_type = component_type_dict.get(d.salary_component)

		if data_list.get(d.name):
			data_list[d.name][component_type] = d.amount
		else:
			data_list.setdefault(
				d.name,
				{
					"employee": d.employee,
					"employee_name": d.employee_name,
					"pf_account": employee_account_dict.get(d.employee),
					component_type: d.amount,
				},
			)

	return data_list


def get_data(filters):
	data = []
	SalarySlip = DocType("Salary Slip")
	SalaryDetail = DocType("Salary Detail")
	SalaryComponent = DocType("Salary Component")

	filter_clauses = get_conditions(filters)
	component_types = ["Provident Fund", "Additional Provident Fund", "Provident Fund Loan"]

	component_type_dict = frappe._dict(
		frappe.qb.from_(SalaryComponent)
		.select(SalaryComponent.name, SalaryComponent.component_type)
		.where(SalaryComponent.component_type.isin(component_types))
		.run()
	)

	if not len(component_type_dict):
		return []

	base_where = SalarySlip.docstatus == 1
	for clause in filter_clauses:
		base_where = base_where & clause

	salary_slips = frappe.qb.from_(SalarySlip).select(SalarySlip.name).where(base_where).run(as_dict=True)

	comp_names = list(component_type_dict.keys())
	entry = (
		frappe.qb.from_(SalarySlip)
		.join(SalaryDetail)
		.on(SalarySlip.name == SalaryDetail.parent)
		.select(
			SalarySlip.name,
			SalarySlip.employee,
			SalarySlip.employee_name,
			SalaryDetail.salary_component,
			SalaryDetail.amount,
		)
		.where(
			(SalaryDetail.parentfield == "deductions")
			& (SalaryDetail.parenttype == "Salary Slip")
			& (SalaryDetail.salary_component.isin(comp_names))
			& base_where
		)
		.run(as_dict=True)
	)

	data_list = prepare_data(entry, component_type_dict)

	for d in salary_slips:
		total = 0
		if data_list.get(d.name):
			employee = {
				"employee": data_list.get(d.name).get("employee"),
				"employee_name": data_list.get(d.name).get("employee_name"),
				"pf_account": data_list.get(d.name).get("pf_account"),
			}

			if data_list.get(d.name).get("Provident Fund"):
				employee["pf_amount"] = data_list.get(d.name).get("Provident Fund")
				total += data_list.get(d.name).get("Provident Fund")

			if data_list.get(d.name).get("Additional Provident Fund"):
				employee["additional_pf"] = data_list.get(d.name).get("Additional Provident Fund")
				total += data_list.get(d.name).get("Additional Provident Fund")

			if data_list.get(d.name).get("Provident Fund Loan"):
				employee["pf_loan"] = data_list.get(d.name).get("Provident Fund Loan")
				total += data_list.get(d.name).get("Provident Fund Loan")

			employee["total"] = total

			data.append(employee)

	return data


@frappe.whitelist()
def get_years() -> str:
	SalarySlip = DocType("Salary Slip")
	year_list = (
		frappe.qb.from_(SalarySlip)
		.select(Extract("year", SalarySlip.end_date).as_("year"))
		.distinct()
		.orderby(Extract("year", SalarySlip.end_date), order=frappe.qb.desc)
		.run(pluck=True)
	)
	if not year_list:
		year_list = [getdate().year]

	return "\n".join(str(year) for year in year_list)
