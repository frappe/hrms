# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe.model.document import Document


class SalaryDetail(Document):
	pass


@frappe.whitelist()
def update_salary_structures(component, field, value):
	salary_details = frappe.get_list(
		"Salary Detail", filters={"salary_component": component}, pluck="name"
	)
	for d in salary_details:
		frappe.db.set_value("Salary Detail", d, field, value)
