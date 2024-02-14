# Copyright (c) 2023, LucrumERP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class SalaryReviseTool(Document):
	def on_submit(self):
		if self.employee_salary_details:
			for salary_detail in self.employee_salary_details:
				if salary_detail.new_salary <= 0:
					frappe.throw(_(f"Employee: <b>{salary_detail.employee_name}</b> Salary cannot be <b> Zero (0) or negative</b>"))
				else:
					ref_ss = frappe.get_doc("Salary Structure Assignment", salary_detail.ref_ss_assignment)
					doc = frappe.new_doc("Salary Structure Assignment")
					doc.employee = ref_ss.employee
					doc.employee_name = ref_ss.employee_name
					doc.department = ref_ss.department_name
					doc.department_name = ref_ss.department_name
					doc.designation = ref_ss.designation
					doc.grade = ref_ss.grade
					doc.salary_structure = ref_ss.salary_structure
					doc.from_date = salary_detail.from_date
					doc.income_tax_slab = ref_ss.income_tax_slab
					doc.company = ref_ss.company
					doc.payroll_payable_account = ref_ss.payroll_payable_account
					doc.currency = ref_ss.currency
					doc.base = salary_detail.new_salary
					doc.variable = salary_detail.new_variable
					doc.amended_from = ref_ss.amended_from
					doc.taxable_earnings_till_date = ref_ss.taxable_earnings_till_date
					doc.tax_deducted_till_date = ref_ss.tax_deducted_till_date
					doc.payroll_cost_centers = ref_ss.payroll_cost_centers
					doc.insert().submit()


@frappe.whitelist()
def load_data(department, branch):
	filters = "AND ssa.docstatus < 2 "
	if department:
		filters += f"AND e.department = '{department}' "
	if branch:
		filters += f"AND e.branch = '{branch}' "
	employees = frappe.db.sql(f"""
		SELECT ssa.base, ssa.from_date, e.name as e_name, e.employee_name, e.designation, e.department, e.branch, e.default_shift, ssa.variable, ssa.name
		FROM `tabEmployee` e
		INNER JOIN `tabSalary Structure Assignment` ssa
		ON e.name = ssa.employee
		INNER JOIN (
			SELECT employee, MAX(creation) AS max_creation
			FROM `tabSalary Structure Assignment`
			GROUP BY employee
		) max_ssa
		ON ssa.employee = max_ssa.employee
		AND ssa.creation = max_ssa.max_creation
		{filters}
	""")
	return employees


@frappe.whitelist()
def fetch_employee_salary(employee):
	doc = frappe.get_doc("Salary Structure Assignment", {"employee": employee}, ["base", "from_date"])
	return [doc.base, doc.from_date]

