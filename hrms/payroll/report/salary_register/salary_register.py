# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from frappe.utils import flt

import erpnext

from hrms.payroll.utils import COMPONENT_PARENTFIELDS

salary_slip = frappe.qb.DocType("Salary Slip")
salary_detail = frappe.qb.DocType("Salary Detail")

EMPLOYER_CONTRIBUTIONS = "employer_contributions"


def execute(filters=None):
	if not filters:
		filters = {}

	currency = None
	if filters.get("currency"):
		currency = filters.get("currency")
	company_currency = erpnext.get_company_currency(filters.get("company"))

	salary_slips = get_salary_slips(filters, company_currency)
	if not salary_slips:
		return [], []

	parentfields = get_active_parentfields(filters)
	components = get_components_by_parentfield(salary_slips, parentfields)
	fieldnames = get_component_fieldnames(components, parentfields)
	columns = get_columns(components, fieldnames)

	component_maps = {
		parentfield: get_salary_slip_details(salary_slips, currency, company_currency, parentfield)
		for parentfield in parentfields
	}

	doj_map = get_employee_doj_map()

	data = []
	for ss in salary_slips:
		row = {
			"salary_slip_id": ss.name,
			"employee": ss.employee,
			"employee_name": ss.employee_name,
			"data_of_joining": doj_map.get(ss.employee),
			"branch": ss.branch,
			"department": ss.department,
			"designation": ss.designation,
			"company": ss.company,
			"start_date": ss.start_date,
			"end_date": ss.end_date,
			"leave_without_pay": ss.leave_without_pay,
			"absent_days": ss.absent_days,
			"payment_days": ss.payment_days,
			"currency": currency or company_currency,
			"total_loan_repayment": ss.total_loan_repayment,
		}

		update_column_width(ss, columns)

		for parentfield in parentfields:
			amounts = component_maps[parentfield].get(ss.name, {})
			for component, amount in amounts.items():
				fieldname = fieldnames.get((parentfield, component))
				if fieldname:
					row[fieldname] = amount

		if components[EMPLOYER_CONTRIBUTIONS]:
			row.update(
				{
					"total_employer_contribution": sum(
						component_maps[EMPLOYER_CONTRIBUTIONS].get(ss.name, {}).values()
					)
				}
			)

		if currency == company_currency:
			row.update(
				{
					"gross_pay": flt(ss.gross_pay) * flt(ss.exchange_rate),
					"total_deduction": (flt(ss.total_deduction) + flt(ss.total_loan_repayment))
					* flt(ss.exchange_rate),
					"net_pay": flt(ss.net_pay) * flt(ss.exchange_rate),
				}
			)

		else:
			row.update(
				{
					"gross_pay": ss.gross_pay,
					"total_deduction": flt(ss.total_deduction) + flt(ss.total_loan_repayment),
					"net_pay": ss.net_pay,
				}
			)

		data.append(row)

	return columns, data


def get_active_parentfields(filters):
	if filters.get("show_employer_contributions"):
		return COMPONENT_PARENTFIELDS

	return tuple(p for p in COMPONENT_PARENTFIELDS if p != EMPLOYER_CONTRIBUTIONS)


def get_component_fieldnames(components, parentfields):
	fieldnames = {}
	used = set()

	for parentfield in parentfields:
		for component in components[parentfield]:
			fieldname = frappe.scrub(component)
			if parentfield == EMPLOYER_CONTRIBUTIONS:
				fieldname = f"employer_contribution_{fieldname}"

			if fieldname in used:
				fieldname = f"{fieldname}_{len(used)}"

			used.add(fieldname)
			fieldnames[(parentfield, component)] = fieldname

	return fieldnames


def get_components_by_parentfield(salary_slips, parentfields):
	rows = get_salary_components(salary_slips)
	components = {parentfield: set() for parentfield in COMPONENT_PARENTFIELDS}
	pay_components = set()

	for parentfield in parentfields:
		for row in rows:
			if row.parentfield != parentfield:
				continue

			if parentfield == EMPLOYER_CONTRIBUTIONS:
				components[parentfield].add(row.salary_component)
			elif row.salary_component not in pay_components:
				components[parentfield].add(row.salary_component)
				pay_components.add(row.salary_component)

	return {parentfield: sorted(names) for parentfield, names in components.items()}


def update_column_width(ss, columns):
	if ss.branch is not None:
		columns[3].update({"width": 120})
	if ss.department is not None:
		columns[4].update({"width": 120})
	if ss.designation is not None:
		columns[5].update({"width": 120})
	if ss.leave_without_pay is not None:
		columns[9].update({"width": 120})


def get_columns(components, fieldnames):
	columns = [
		{
			"label": _("Salary Slip ID"),
			"fieldname": "salary_slip_id",
			"fieldtype": "Link",
			"options": "Salary Slip",
			"width": 150,
		},
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
			"width": 140,
		},
		{
			"label": _("Date of Joining"),
			"fieldname": "data_of_joining",
			"fieldtype": "Date",
			"width": 80,
		},
		{
			"label": _("Branch"),
			"fieldname": "branch",
			"fieldtype": "Link",
			"options": "Branch",
			"width": -1,
		},
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": -1,
		},
		{
			"label": _("Designation"),
			"fieldname": "designation",
			"fieldtype": "Link",
			"options": "Designation",
			"width": 120,
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 120,
		},
		{
			"label": _("Start Date"),
			"fieldname": "start_date",
			"fieldtype": "Data",
			"width": 80,
		},
		{
			"label": _("End Date"),
			"fieldname": "end_date",
			"fieldtype": "Data",
			"width": 80,
		},
		{
			"label": _("Leave Without Pay"),
			"fieldname": "leave_without_pay",
			"fieldtype": "Float",
			"width": 50,
		},
		{
			"label": _("Absent Days"),
			"fieldname": "absent_days",
			"fieldtype": "Float",
			"width": 50,
		},
		{
			"label": _("Payment Days"),
			"fieldname": "payment_days",
			"fieldtype": "Float",
			"width": 120,
		},
	]

	for earning in components["earnings"]:
		columns.append(
			{
				"label": earning,
				"fieldname": fieldnames[("earnings", earning)],
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			}
		)

	columns.append(
		{
			"label": _("Gross Pay"),
			"fieldname": "gross_pay",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		}
	)

	for deduction in components["deductions"]:
		columns.append(
			{
				"label": deduction,
				"fieldname": fieldnames[("deductions", deduction)],
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			}
		)

	if "lending" in frappe.get_installed_apps():
		columns.append(
			{
				"label": _("Loan Repayment"),
				"fieldname": "total_loan_repayment",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			}
		)

	columns.extend(
		[
			{
				"label": _("Total Deduction"),
				"fieldname": "total_deduction",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
			{
				"label": _("Net Pay"),
				"fieldname": "net_pay",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
		]
	)

	for contribution in components[EMPLOYER_CONTRIBUTIONS]:
		columns.append(
			{
				"label": contribution,
				"fieldname": fieldnames[(EMPLOYER_CONTRIBUTIONS, contribution)],
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			}
		)

	if components[EMPLOYER_CONTRIBUTIONS]:
		columns.append(
			{
				"label": _("Total Employer Contribution"),
				"fieldname": "total_employer_contribution",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			}
		)

	columns.append(
		{
			"label": _("Currency"),
			"fieldtype": "Data",
			"fieldname": "currency",
			"options": "Currency",
			"hidden": 1,
		}
	)
	return columns


def get_salary_components(salary_slips):
	return (
		frappe.qb.from_(salary_detail)
		.where((salary_detail.amount != 0) & (salary_detail.parent.isin([d.name for d in salary_slips])))
		.select(salary_detail.parentfield, salary_detail.salary_component)
		.distinct()
	).run(as_dict=True)


def get_salary_slips(filters, company_currency):
	doc_status = {"Draft": 0, "Submitted": 1, "Cancelled": 2}

	query = frappe.qb.from_(salary_slip).select(salary_slip.star)

	if filters.get("docstatus"):
		query = query.where(salary_slip.docstatus == doc_status[filters.get("docstatus")])

	if filters.get("from_date"):
		query = query.where(salary_slip.start_date >= filters.get("from_date"))

	if filters.get("to_date"):
		query = query.where(salary_slip.end_date <= filters.get("to_date"))

	if filters.get("company"):
		query = query.where(salary_slip.company == filters.get("company"))

	if filters.get("employee"):
		query = query.where(salary_slip.employee == filters.get("employee"))

	if filters.get("currency") and filters.get("currency") != company_currency:
		query = query.where(salary_slip.currency == filters.get("currency"))

	if filters.get("department"):
		query = query.where(salary_slip.department == filters["department"])

	if filters.get("designation"):
		query = query.where(salary_slip.designation == filters["designation"])

	if filters.get("branch"):
		query = query.where(salary_slip.branch == filters["branch"])

	salary_slips = query.run(as_dict=1)

	return salary_slips or []


def get_employee_doj_map():
	employee = frappe.qb.DocType("Employee")

	result = (frappe.qb.from_(employee).select(employee.name, employee.date_of_joining)).run()

	return frappe._dict(result)


def get_salary_slip_details(salary_slips, currency, company_currency, parentfield):
	salary_slips = [ss.name for ss in salary_slips]

	result = (
		frappe.qb.from_(salary_slip)
		.join(salary_detail)
		.on(salary_slip.name == salary_detail.parent)
		.where((salary_detail.parent.isin(salary_slips)) & (salary_detail.parentfield == parentfield))
		.select(
			salary_detail.parent,
			salary_detail.salary_component,
			salary_detail.amount,
			salary_slip.exchange_rate,
		)
	).run(as_dict=1)

	ss_map = {}

	for d in result:
		ss_map.setdefault(d.parent, frappe._dict()).setdefault(d.salary_component, 0.0)
		if currency == company_currency:
			ss_map[d.parent][d.salary_component] += flt(d.amount) * flt(
				d.exchange_rate if d.exchange_rate else 1
			)
		else:
			ss_map[d.parent][d.salary_component] += flt(d.amount)

	return ss_map
