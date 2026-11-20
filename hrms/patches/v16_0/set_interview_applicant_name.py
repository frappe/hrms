import frappe
from frappe.query_builder.functions import IfNull
from frappe.query_builder.terms import SubQuery


def execute():
	frappe.reload_doc("hr", "doctype", "interview")

	Interview = frappe.qb.DocType("Interview")
	Applicant = frappe.qb.DocType("Job Applicant")
	applicant_name = (
		frappe.qb.from_(Applicant)
		.select(Applicant.applicant_name)
		.where(Applicant.name == Interview.job_applicant)
	)
	(
		frappe.qb.update(Interview)
		.set(Interview.applicant_name, SubQuery(applicant_name))
		.where(IfNull(Interview.applicant_name, "") == "")
		.where(Interview.job_applicant.isin(frappe.qb.from_(Applicant).select(Applicant.name)))
	).run()
