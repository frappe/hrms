import frappe


def execute():
	salary_structure = frappe.qb.DocType("Salary Structure")
	frappe.qb.update(salary_structure).set(salary_structure.payroll_frequency, "").where(
		salary_structure.salary_slip_based_on_timesheet == 1
	).run()
