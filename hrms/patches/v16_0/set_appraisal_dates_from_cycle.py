import frappe


def execute():
	Appraisal = frappe.qb.DocType("Appraisal")
	for cycle in frappe.get_all("Appraisal Cycle", fields=["name", "start_date", "end_date"]):
		(
			frappe.qb.update(Appraisal)
			.set(Appraisal.start_date, cycle.start_date)
			.set(Appraisal.end_date, cycle.end_date)
			.where(Appraisal.appraisal_cycle == cycle.name)
		).run()
