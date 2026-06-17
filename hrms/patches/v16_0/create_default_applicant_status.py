# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe


def execute():
	"""
	Convert Job Applicant's hardcoded `status` Select field into a configurable
	Link to the new `Job Applicant Status` doctype.
	Seeds default Applicant Status records matching the previous Select options
	so existing Job Applicant records remain valid without any data changes.
	"""
	frappe.reload_doc("hr", "doctype", "job_applicant_status")
	frappe.reload_doc("hr", "doctype", "job_applicant")

	create_default_applicant_statuses()


def create_default_applicant_statuses():
	default_statuses = [
		{"status_name": "Open", "sequence": 1, "is_closed_status": 0, "color": "#bd3e0c"},
		{"status_name": "Replied", "sequence": 2, "is_closed_status": 0, "color": "#bd3e0c"},
		{"status_name": "Shortlisted", "sequence": 3, "is_closed_status": 0, "color": "#0070cc"},
		{"status_name": "Accepted", "sequence": 4, "is_closed_status": 1, "color": "#16794c"},
		{"status_name": "Rejected", "sequence": 5, "is_closed_status": 1, "color": "#b52a2a"},
		{"status_name": "Hold", "sequence": 6, "is_closed_status": 0, "color": "#b52a2a"},
	]

	for status in default_statuses:
		if frappe.db.exists("Job Applicant Status", status["status_name"]):
			# Update sequence in case the record was seeded with an older order.
			frappe.db.set_value("Job Applicant Status", status["status_name"], "sequence", status["sequence"])
		else:
			frappe.get_doc({"doctype": "Job Applicant Status", **status}).insert(ignore_permissions=True)
