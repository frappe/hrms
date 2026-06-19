# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.utils import getdate


def get_employee_records(company):
	return frappe.get_all(
		"Employee",
		filters={"status": "Active", "company": company},
		fields=[
			"name",
			"employee_name",
			"date_of_joining",
			"final_confirmation_date",
			"employment_type",
			"company",
		],
	)


def setup_leave_and_attendance(company):
	from hrms.hrms_setup.demo_attendance import generate_attendance

	employees = get_employee_records(company)

	leave_period = frappe.db.get_value(
		"Leave Period",
		{"company": company},
		"name",
		order_by="from_date DESC",
	)
	if not leave_period:
		leave_period = create_current_year_leave_period(company)

	leave_period_doc = frappe.get_doc("Leave Period", leave_period)
	generate_attendance(employees, leave_period_doc)


def create_current_year_leave_period(company):
	from frappe.desk.page.setup_wizard.setup_wizard import make_records

	current_year = getdate().year
	leave_period_name = f"Leave Period {current_year}-{current_year + 1}"
	if not frappe.db.exists("Leave Period", leave_period_name):
		make_records(
			[
				{
					"doctype": "Leave Period",
					"leave_period_name": leave_period_name,
					"from_date": f"{current_year}-01-01",
					"to_date": f"{current_year}-12-31",
					"company": company,
				}
			]
		)

	return leave_period_name
