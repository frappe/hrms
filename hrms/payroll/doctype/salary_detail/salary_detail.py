# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe.model.document import Document


class SalaryDetail(Document):
	pass


@frappe.whitelist()
def update_salary_structures(component, field, value):
	SalaryDetail = frappe.qb.DocType("Salary Detail")
	SalaryStructure = frappe.qb.DocType("Salary Structure")
	frappe.qb.update(SalaryDetail).inner_join(SalaryStructure).on(
		SalaryDetail.parent == SalaryStructure.name
	).set(SalaryDetail[field], value).where(
		(SalaryDetail.salary_component == component) & (SalaryStructure.docstatus == 1)
	).run()
