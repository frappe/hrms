# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.utils import getdate


def setup_salary_structure_assignments(company):
	company = frappe.db.exists("Company", company) or company
	if not frappe.db.exists("Company", company):
		first_company = frappe.get_all("Company", pluck="name")
		if not first_company:
			return
		company = first_company[0]

	salary_structures = frappe.get_all(
		"Salary Structure",
		filters={"company": company, "docstatus": 1, "is_active": "Yes"},
		pluck="name",
	)

	if not salary_structures:
		return

	employees = frappe.get_all(
		"Employee",
		filters={"status": "Active", "company": company},
		fields=["name", "employee_name", "designation", "department"],
	)

	if not employees:
		return

	for emp in employees:
		if not emp.designation:
			continue

		ss_name = get_salary_structure_for_employee(emp.designation, salary_structures)
		if not ss_name:
			continue

		if frappe.db.exists("Salary Structure Assignment", {"employee": emp.name, "docstatus": 1}):
			continue

		try:
			assignment = frappe.get_doc(
				{
					"doctype": "Salary Structure Assignment",
					"employee": emp.name,
					"salary_structure": ss_name,
					"company": company,
					"department": emp.department,
					"from_date": f"{getdate().year}-01-01",
					"currency": get_salary_structure_currency(ss_name),
					"payroll_payable_account": get_payroll_payable_account(company),
				}
			)
			assignment.insert(ignore_permissions=True)
			assignment.submit()
		except Exception:
			continue


def get_salary_structure_for_employee(designation, salary_structures):
	designation = designation.lower()
	for salary_structure in salary_structures:
		if salary_structure.lower() in designation or designation in salary_structure.lower():
			return salary_structure

	return salary_structures[0] if salary_structures else None


def get_salary_structure_currency(salary_structure):
	return frappe.db.get_value("Salary Structure", salary_structure, "currency") or "USD"


def get_payroll_payable_account(company):
	accounts = frappe.get_all(
		"Account",
		filters={"company": company, "account_name": ["like", "%Payroll Payable%"]},
		pluck="name",
	)
	return accounts[0] if accounts else None


def setup_leave_and_attendance(company):
	from hrms.hrms_setup.demo_attendance import (
		create_leave_allocations,
		create_leave_applications,
		generate_attendance,
	)

	employees = frappe.get_all(
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
