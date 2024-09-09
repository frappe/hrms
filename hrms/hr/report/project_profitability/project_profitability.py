# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint, flt


def execute(filters=None):
	data = get_data(filters)
	columns = get_columns()
	charts = get_chart_data(data)
	return columns, data, None, charts


def get_data(filters):
	data = get_rows(filters)
	data = calculate_cost_and_profit(data)
	return data


def get_rows(filters):
	Timesheet = frappe.qb.DocType("Timesheet")
	SalarySlip = frappe.qb.DocType("Salary Slip")
	SalesInvoice = frappe.qb.DocType("Sales Invoice")
	SalesInvoiceTimesheet = frappe.qb.DocType("Sales Invoice Timesheet")
	SalarySlipTimesheet = frappe.qb.DocType("Salary Slip Timesheet")

	query = (
		frappe.qb.from_(SalarySlipTimesheet)
		.inner_join(Timesheet)
		.on(SalarySlipTimesheet.time_sheet == Timesheet.name)
		.inner_join(SalarySlip)
		.on(SalarySlipTimesheet.parent == SalarySlip.name)
		.inner_join(SalesInvoiceTimesheet)
		.on(SalesInvoiceTimesheet.time_sheet == Timesheet.name)
		.inner_join(SalesInvoice)
		.on(SalesInvoiceTimesheet.parent == SalesInvoice.name)
		.select(
			SalesInvoice.customer_name,
			SalesInvoice.base_grand_total,
			SalesInvoice.name.as_("voucher_no"),
			Timesheet.employee,
			Timesheet.title.as_("employee_name"),
			Timesheet.parent_project.as_("project"),
			Timesheet.start_date,
			Timesheet.end_date,
			Timesheet.total_billed_hours,
			Timesheet.name.as_("timesheet"),
			SalarySlip.base_gross_pay,
			SalarySlip.total_working_days,
			Timesheet.total_billed_hours,
		)
		.distinct()
		.where((SalesInvoice.docstatus == 1) & (SalarySlip.docstatus == 1))
	)

	if filters.get("company"):
		query = query.where(Timesheet.company == filters.get("company"))

	if filters.get("start_date"):
		query = query.where(Timesheet.start_date >= filters.get("start_date"))

	if filters.get("end_date"):
		query = query.where(Timesheet.end_date <= filters.get("end_date"))

	if filters.get("customer"):
		query = query.where(SalesInvoice.customer == filters.get("customer"))

	if filters.get("employee"):
		query = query.where(Timesheet.employee == filters.get("employee"))

	if filters.get("project"):
		query = query.where(Timesheet.parent_project == filters.get("project"))

	return query.run(as_dict=True)


def calculate_cost_and_profit(data):
	standard_working_hours = get_standard_working_hours()
	precision = cint(frappe.db.get_default("float_precision")) or 2

	for row in data:
		row.utilization = flt(
			flt(row.total_billed_hours) / (flt(row.total_working_days) * flt(standard_working_hours)),
			precision,
		)
		row.fractional_cost = flt(flt(row.base_gross_pay) * flt(row.utilization), precision)

		row.profit = flt(
			flt(row.base_grand_total) - flt(row.base_gross_pay) * flt(row.utilization), precision
		)

	return data


def get_standard_working_hours() -> float | None:
	standard_working_hours = frappe.db.get_single_value("HR Settings", "standard_working_hours")
	if not standard_working_hours:
		frappe.throw(
			_("The metrics for this report are calculated based on the {0}. Please set {0} in {1}.").format(
				frappe.bold(_("Standard Working Hours")),
				frappe.utils.get_link_to_form("HR Settings", "HR Settings"),
			)
		)

	return standard_working_hours


def get_chart_data(data):
	if not data:
		return None

	labels = []
	utilization = []

	for entry in data:
		labels.append(f"{entry.get('employee_name')} - {entry.get('end_date')}")
		utilization.append(entry.get("utilization"))

	charts = {
		"data": {"labels": labels, "datasets": [{"name": "Utilization", "values": utilization}]},
		"type": "bar",
		"colors": ["#84BDD5"],
	}
	return charts


def get_columns():
	return [
		{
			"fieldname": "customer_name",
			"label": _("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			"width": 150,
		},
		{
			"fieldname": "employee",
			"label": _("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 130,
		},
		{"fieldname": "employee_name", "label": _("Employee Name"), "fieldtype": "Data", "width": 120},
		{
			"fieldname": "voucher_no",
			"label": _("Sales Invoice"),
			"fieldtype": "Link",
			"options": "Sales Invoice",
			"width": 120,
		},
		{
			"fieldname": "timesheet",
			"label": _("Timesheet"),
			"fieldtype": "Link",
			"options": "Timesheet",
			"width": 120,
		},
		{
			"fieldname": "project",
			"label": _("Project"),
			"fieldtype": "Link",
			"options": "Project",
			"width": 100,
		},
		{
			"fieldname": "base_grand_total",
			"label": _("Bill Amount"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 100,
		},
		{
			"fieldname": "base_gross_pay",
			"label": _("Cost"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 100,
		},
		{
			"fieldname": "profit",
			"label": _("Profit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 100,
		},
		{"fieldname": "utilization", "label": _("Utilization"), "fieldtype": "Percentage", "width": 100},
		{
			"fieldname": "fractional_cost",
			"label": _("Fractional Cost"),
			"fieldtype": "Int",
			"width": 120,
		},
		{
			"fieldname": "total_billed_hours",
			"label": _("Total Billed Hours"),
			"fieldtype": "Int",
			"width": 150,
		},
		{"fieldname": "start_date", "label": _("Start Date"), "fieldtype": "Date", "width": 100},
		{"fieldname": "end_date", "label": _("End Date"), "fieldtype": "Date", "width": 100},
		{
			"label": _("Currency"),
			"fieldname": "currency",
			"fieldtype": "Link",
			"options": "Currency",
			"width": 80,
		},
	]
