import frappe


def execute():
	frappe.reload_doc("hr", "doctype", "interview")

	frappe.db.sql(
		"""
		UPDATE `tabInterview` AS interview
		JOIN `tabJob Applicant` AS applicant ON applicant.name = interview.job_applicant
		SET interview.applicant_name = applicant.applicant_name
		WHERE IFNULL(interview.applicant_name, '') = ''
		"""
	)
