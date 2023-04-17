import frappe


def execute():
	Offer = frappe.qb.DocType("Job Offer")
	Applicant = frappe.qb.DocType("Job Applicant")

	(
		frappe.qb.update(Offer)
		.inner_join(Applicant)
		.on(Applicant.name == Offer.job_applicant)
		.set(Offer.applicant_email, Applicant.email_id)
		.where(Offer.applicant_email.isnull())
	).run()
