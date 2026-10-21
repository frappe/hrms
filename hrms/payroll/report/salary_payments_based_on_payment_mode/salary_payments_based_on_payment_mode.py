# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.utils import flt

import erpnext

from hrms.payroll.utils import get_conditions

MODE_NOT_SET = "mode_not_set"


def execute(filters=None):
	salary_slips = get_salary_slips(filters)
	mode_of_payments = get_payment_modes(salary_slips)

	if not len(mode_of_payments):
		return [], []

	columns = get_columns(filters, mode_of_payments)
	data, total_rows, report_summary = get_data(filters, mode_of_payments, salary_slips)
	chart = get_chart(mode_of_payments, total_rows)

	return columns, data, None, chart, report_summary


def get_columns(filters, mode_of_payments):
	columns = [
		{
			"label": _("Branch"),
			"options": "Branch",
			"fieldname": "branch",
			"fieldtype": "Link",
			"width": 200,
		}
	]

	for mode in mode_of_payments:
		columns.append(
			{"label": get_mode_label(mode), "fieldname": mode, "fieldtype": "Currency", "width": 160}
		)

	columns.append({"label": _("Total"), "fieldname": "total", "fieldtype": "Currency", "width": 140})

	return columns


def get_salary_slips(filters):
	SalarySlip = DocType("Salary Slip")

	base_where = SalarySlip.docstatus == 1
	for clause in get_conditions(filters):
		base_where = base_where & clause

	salary_slips = (
		frappe.qb.get_query(
			"Salary Slip",
			fields=["branch", "mode_of_payment", "base_net_pay", "base_gross_pay"],
			ignore_permissions=False,
		)
		.where(base_where)
		.run(as_dict=True)
	)
	for slip in salary_slips:
		slip.mode_of_payment = slip.mode_of_payment or MODE_NOT_SET

	return salary_slips


def get_payment_modes(salary_slips):
	return sorted({slip.mode_of_payment for slip in salary_slips})


def get_mode_label(mode):
	return _("Not Set") if mode == MODE_NOT_SET else _(mode)


def prepare_data(salary_slips):
	branch_wise_entries = {}
	gross_pay = 0

	for d in salary_slips:
		gross_pay += flt(d.base_gross_pay)
		modes = branch_wise_entries.setdefault(d.branch, {})
		modes[d.mode_of_payment] = flt(modes.get(d.mode_of_payment)) + flt(d.base_net_pay)

	return branch_wise_entries, gross_pay


def get_data(filters, mode_of_payments, salary_slips):
	data = []

	branch_wise_entries, gross_pay = prepare_data(salary_slips)

	for branch, modes in branch_wise_entries.items():
		total = 0
		row = {"branch": branch}
		for mode in mode_of_payments:
			if modes.get(mode):
				row[mode] = modes.get(mode)
				total += modes.get(mode)

		row["total"] = total
		data.append(row)

	total_row = get_total_based_on_mode_of_payment(data, mode_of_payments)
	total_deductions = gross_pay - total_row.get("total")

	report_summary = []

	if data:
		data.append(total_row)
		data.append({})
		data.append({"branch": "Total Gross Pay", "total": gross_pay})
		data.append({"branch": "Total Deductions", "total": total_deductions})
		data.append({"branch": "Total Net Pay", "total": total_row.get("total")})

		currency = erpnext.get_company_currency(filters.company)
		report_summary = get_report_summary(gross_pay, total_deductions, total_row.get("total"), currency)

	return data, total_row, report_summary


def get_total_based_on_mode_of_payment(data, mode_of_payments):
	total = 0
	total_row = {"branch": "Total"}
	for mode in mode_of_payments:
		sum_of_payment = sum([detail[mode] for detail in data if mode in detail.keys()])
		total_row[mode] = sum_of_payment
		total += sum_of_payment

	total_row["total"] = total
	return total_row


def get_report_summary(gross_pay, total_deductions, net_pay, currency):
	return [
		{
			"value": gross_pay,
			"label": _("Total Gross Pay"),
			"indicator": "Green",
			"datatype": "Currency",
			"currency": currency,
		},
		{
			"value": total_deductions,
			"label": _("Total Deduction"),
			"datatype": "Currency",
			"indicator": "Red",
			"currency": currency,
		},
		{
			"value": net_pay,
			"label": _("Total Net Pay"),
			"datatype": "Currency",
			"indicator": "Blue",
			"currency": currency,
		},
	]


def get_chart(mode_of_payments, data):
	if data:
		values = []
		labels = []

		for mode in mode_of_payments:
			values.append(data[mode])
			labels.append([get_mode_label(mode)])

		chart = {"data": {"labels": labels, "datasets": [{"name": "Mode Of Payments", "values": values}]}}
		chart["type"] = "bar"
		return chart
