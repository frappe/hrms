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

	employee = frappe.db.get_all(
		"Employee",
		filters={"name": employee},
		fields=[
			"date_of_joining",
			"relieving_date",
			"employee_name",
			"resignation_letter_date",
			"notice_number_of_days",
		],
	)

	details = {
		"date_of_joining": employee[0].get("date_of_joining"),
		"relieving_date": employee[0].get("relieving_date"),
		"employee_name": employee[0].get("employee_name"),
		"resignation_letter_date": employee[0].get("resignation_date"),
		"notice_number_of_days": employee[0].get("notice_number_of_days"),
		"payroll_frequency": payroll_frequency,
	}
	return details


@frappe.whitelist()
def calculate_to_date(payroll_frequency, from_date, number_of_withholding_cycles):
	if payroll_frequency == "Monthly":
		to_date = frappe.utils.add_months(from_date, months=int(number_of_withholding_cycles))
	elif payroll_frequency == "Bimonthly":
		to_date = frappe.utils.add_months(from_date, months=int(number_of_withholding_cycles) * 2)
	elif payroll_frequency == "Weekly":
		to_date = frappe.utils.add_days(from_date, days=int(number_of_withholding_cycles) * 7)
	elif payroll_frequency == "Fortnightly":
		to_date = frappe.utils.add_days(from_date, days=int(number_of_withholding_cycles) * 14)
	elif payroll_frequency == "Daily":
		to_date = frappe.utils.add_days(from_date, days=int(number_of_withholding_cycles))

	return {"to_date": to_date}
