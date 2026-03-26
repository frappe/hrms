import frappe


def execute():
	PayrollEntry = frappe.qb.DocType("Payroll Entry")

	status = (
		frappe.qb.terms.Case()
		.when(PayrollEntry.docstatus == 0, "Draft")
		.when(PayrollEntry.docstatus == 1, "Submitted")
		.else_("Cancelled")
	)

	(frappe.qb.update(PayrollEntry).set("status", status).where(PayrollEntry.status.isnull())).run()
