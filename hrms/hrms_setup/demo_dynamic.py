# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.utils import getdate


def setup_salary_structure_assignments(company):
	from hrms.hrms_setup.demo import get_demo_records

	for record in get_demo_records("salary_structure_assignment"):
		if record.get("company") != company or not frappe.db.exists("Company", record.get("company")):
			continue

		if not frappe.db.exists("Employee", record.get("employee")):
			continue

		record = get_valid_salary_structure_assignment_record(record)

		if not frappe.db.exists("Salary Structure", record.get("salary_structure")):
			continue

		if frappe.db.exists(
			"Salary Structure Assignment",
			{
				"employee": record.get("employee"),
				"from_date": record.get("from_date"),
				"docstatus": 1,
			},
		):
			continue

		create_and_submit_doc(record)


def get_valid_salary_structure_assignment_record(record):
	record = record.copy()
	joining_date = frappe.db.get_value("Employee", record.get("employee"), "date_of_joining")
	if joining_date and getdate(record.get("from_date")) < getdate(joining_date):
		record["from_date"] = joining_date

	return record


def create_and_submit_doc(record):
	previous_in_import = getattr(frappe.flags, "in_import", False)
	if record.get("name"):
		frappe.flags.in_import = True

	try:
		doc = frappe.get_doc(record)
		doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
		if doc.docstatus == 0:
			doc.submit()
	except Exception:
		frappe.log_error(
			title=f"Failed to create HR demo {record.get('doctype')}",
			message=frappe.get_traceback(),
		)
	finally:
		frappe.flags.in_import = previous_in_import


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
	from hrms.hrms_setup.demo_attendance import (
		create_leave_allocations,
		create_leave_applications,
		generate_attendance,
	)

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
	create_leave_allocations(employees, leave_period_doc, company)
	create_leave_applications(employees, leave_period_doc)
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
