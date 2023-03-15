import frappe


def execute():
	ss = frappe.qb.DocType("Salary Structure").as_("ss")
	sd = frappe.qb.DocType("Salary Detail").as_("sd")

	(
		frappe.qb.update(sd)
		.inner_join(ss)
		.on(ss.name == sd.parent)
		.set(sd.docstatus, 1)
		.where((ss.docstatus == 1) & (sd.parenttype == "Salary Structure"))
	).run()
