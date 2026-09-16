import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Employee": [
				{
					"fieldname": "job_applicant",
					"fieldtype": "Link",
					"label": _("Job Applicant"),
					"options": "Job Applicant",
					"insert_after": "employment_details",
					"depends_on": "eval:doc.job_applicant",
					"read_only": 1,
				},
				{
					"fieldname": "job_offer",
					"fieldtype": "Link",
					"label": _("Job Offer"),
					"options": "Job Offer",
					"insert_after": "job_applicant",
					"depends_on": "eval:doc.job_offer",
					"read_only": 1,
				},
			]
		}
	)

	set_job_offer_in_employee()


def set_job_offer_in_employee():
	employees = frappe.get_all(
		"Employee", filters={"job_applicant": ["is", "set"]}, fields=["name", "job_applicant"]
	)

	for employee in employees:
		job_offer = frappe.db.get_value(
			"Job Offer", {"job_applicant": employee.job_applicant, "docstatus": ["!=", 2]}, "name"
		)
		if job_offer:
			frappe.db.set_value("Employee", employee.name, "job_offer", job_offer, update_modified=False)
