import frappe

from hrms.hr.doctype.employee_onboarding.onboarding_activities import (
	add_standard_activities,
	has_standard_activities,
)


def execute():
	for name in frappe.get_all(
		"Employee Boarding Activity",
		filters={"parenttype": "Employee Boarding Template", "parentfield": "onboarding_activities"},
		pluck="parent",
		distinct=True,
	):
		template = frappe.get_doc("Employee Boarding Template", name)
		if has_standard_activities(template):
			continue
		add_standard_activities(template)
		template.flags.ignore_links = template.flags.ignore_mandatory = True
		template.save(ignore_permissions=True)
