# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SalaryWithholding(Document):
	pass


@frappe.whitelist()
def get_employee_details(employee):
	salary_structure_assignment = frappe.db.get_value(
		"Salary Structure Assignment",
		{"employee": employee},
		"salary_structure",
	)

	payroll_frequency = frappe.db.get_value(
		"Salary Structure", salary_structure_assignment, "payroll_frequency"
	)

	employee_details = frappe.db.get_value(
		"Employee",
		{"name": employee},
		[
			"date_of_joining",
			"relieving_date",
			"employee_name",
			"resignation_letter_date",
			"notice_number_of_days",
		],
		as_dict=True,
	)

	details = {
		"date_of_joining": employee_details.date_of_joining,
		"date_of_relieving": employee_details.relieving_date,
		"employee_name": employee_details.employee_name,
		"resignation_letter_date": employee_details.resignation_date,
		"notice_number_of_days": employee_details.notice_number_of_days,
		"payroll_frequency": payroll_frequency,
	}
	return details


def add_months_to_date(from_date, months, n):
	return frappe.utils.add_months(from_date, months=int(months) * n)


def add_days_to_date(from_date, days, n):
	return frappe.utils.add_days(from_date, days=int(days) * n)


@frappe.whitelist()
def calculate_to_date(payroll_frequency, from_date, number_of_withholding_cycles):
	if payroll_frequency == "Monthly":
		return add_months_to_date(from_date, int(number_of_withholding_cycles), 1)
	elif payroll_frequency == "Bimonthly":
		return add_months_to_date(from_date, int(number_of_withholding_cycles), 2)
	elif payroll_frequency == "Weekly":
		return add_days_to_date(from_date, int(number_of_withholding_cycles), 7)
	elif payroll_frequency == "Fortnightly":
		return add_days_to_date(from_date, int(number_of_withholding_cycles), 14)
	elif payroll_frequency == "Daily":
		return add_days_to_date(from_date, int(number_of_withholding_cycles), 1)


@frappe.whitelist()
def get_salary_withholding_cycles_and_to_date(
	payroll_frequency, number_of_withholding_cycles, from_date=None
):
	cycles = []

	withholding_to_date = calculate_to_date(payroll_frequency, from_date, number_of_withholding_cycles)
	cycle_from_date = from_date
	cycle_to_date = from_date

	while cycle_to_date < add_days_to_date(withholding_to_date, -1, 1):
		res = calculate_to_date(payroll_frequency, cycle_from_date, 1)
		cycle_to_date = add_days_to_date(res, -1, 1)

		cycles.append({"from_date": cycle_from_date, "to_date": cycle_to_date})
		cycle_from_date = res

	return {"cycles": cycles, "to_date": withholding_to_date}
