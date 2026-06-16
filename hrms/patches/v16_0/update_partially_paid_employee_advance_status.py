import frappe


def execute():
	frappe.reload_doc("hr", "doctype", "employee_advance")

	advance = frappe.qb.DocType("Employee Advance")
	(
		frappe.qb.update(advance)
		.set(advance.status, "Partially Paid")
		.where(
			(advance.docstatus == 1)
			& (advance.paid_amount > 0)
			& (advance.paid_amount < advance.advance_amount)
			& (advance.status == "Unpaid")
		)
	).run()
