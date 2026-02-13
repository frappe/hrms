import frappe
from frappe.query_builder.functions import IfNull


def execute():
	EmployeeAdvance = frappe.qb.DocType("Employee Advance")
	Company = frappe.qb.DocType("Company")

	(
		frappe.qb.update(EmployeeAdvance)
		.join(Company)
		.on(EmployeeAdvance.company == Company.name)
		.set(EmployeeAdvance.base_paid_amount, EmployeeAdvance.paid_amount)
		.where(
			(EmployeeAdvance.currency == Company.default_currency)
			& (IfNull(EmployeeAdvance.paid_amount, 0) != 0)
			& (IfNull(EmployeeAdvance.base_paid_amount, 0) == 0)
		)
	).run()
