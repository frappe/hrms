import frappe


def add_hrms_boot_info(bootinfo):
	bootinfo.job_applicant_statuses = frappe.get_all(
		"Job Applicant Status",
		fields=["status_name", "color"],
		order_by="sequence asc",
	)
