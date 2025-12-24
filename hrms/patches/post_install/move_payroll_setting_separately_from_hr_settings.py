# Copyright (c) 2019, Frappe and Contributors
# License: GNU General Public License v3. See license.txt


import frappe


def execute():
	singles = frappe.qb.DocType("Singles")
	fields_to_move = [
		"encrypt_salary_slips_in_emails",
		"email_salary_slip_to_employee",
		"daily_wages_fraction_for_half_day",
		"disable_rounded_total",
		"include_holidays_in_total_working_days",
		"max_working_hours_against_timesheet",
		"payroll_based_on",
		"password_policy",
	]
	data = (
		frappe.qb.from_(singles)
		.select(singles.field, singles.value)
		.where(singles.doctype == "HR Settings")
		.where(singles.field.isin(fields_to_move))
	).run(as_dict=True)

	for d in data:
		frappe.db.set_value("Payroll Settings", None, d.field, d.value)
