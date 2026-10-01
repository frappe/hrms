# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Extract
from frappe.utils import getdate


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
