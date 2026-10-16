import frappe


def execute():
	job_offer = frappe.qb.DocType("Job Offer")
	(
		frappe.qb.update(job_offer)
		.set(job_offer.status, "Draft")
		.where(job_offer.docstatus == 0)
		.where(job_offer.status.isnull() | job_offer.status.isin(["", "Awaiting Response"]))
	).run()
