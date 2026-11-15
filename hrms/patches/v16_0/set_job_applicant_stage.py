import frappe

from hrms.hr.doctype.job_applicant.job_applicant import get_stage

BATCH_SIZE = 500


def execute():
	frappe.reload_doc("hr", "doctype", "job_applicant")

	applicants = frappe.get_all("Job Applicant", fields=["name", "status", "stage"], order_by="creation")
	for start in range(0, len(applicants), BATCH_SIZE):
		for applicant in applicants[start : start + BATCH_SIZE]:
			stage = get_stage(applicant)
			if stage != applicant.stage:
				frappe.db.set_value("Job Applicant", applicant.name, "stage", stage, update_modified=False)

		frappe.db.commit()  # nosemgrep
